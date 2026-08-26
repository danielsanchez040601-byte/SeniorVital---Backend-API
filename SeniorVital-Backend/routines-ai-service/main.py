"""Microservicio de generación de rutinas de ejercicio con IA.

Utiliza Ollama (phi3:mini) para generar rutinas personalizadas
basadas en el perfil de salud del usuario y los ejercicios
disponibles en el catálogo, respetando restricciones médicas.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
from datetime import date
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
import httpx

from seniorvital_shared import get_pool, init_pool, close_pool, publish_event

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "google/gemma-4-31b:free")
OLLAMA_MODEL = DEFAULT_LLM_MODEL

DEFAULT_ROUTINE = {
    "exercises": [
        {"name": "Caminata ligera", "sets": 1, "reps": 10, "duration_min": 5},
        {"name": "Estiramiento de brazos", "sets": 2, "reps": 8, "duration_min": 3},
        {"name": "Respiración profunda", "sets": 1, "reps": 5, "duration_min": 2},
    ],
    "warmup": [{"name": "Rotación de cuello", "sets": 1, "reps": 5}],
}


class GenerateRequest(BaseModel):
    """Solicitud para generar una rutina de ejercicios."""
    user_id: str
    force: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida del servicio: inicializa y cierra el pool de conexiones."""
    await init_pool(owner="routines")
    yield
    await close_pool(owner="routines")


app = FastAPI(
    title="Routines AI Service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
)


async def call_ollama(prompt: str) -> dict:
    """Envía un prompt a Ollama y parsea la respuesta JSON.

    :param prompt: Texto del prompt para el modelo.
    :raises httpx.HTTPError: Si la llamada a Ollama falla.
    :return: Diccionario con la respuesta parseada.
    """
    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        )
        resp.raise_for_status()
        return json.loads(resp.json()["response"])


def build_prompt(profile: dict, safe_exercises: list) -> str:
    """Construye el prompt para Ollama con el perfil y ejercicios seguros.

    :param profile: Perfil de salud del usuario.
    :param safe_exercises: Lista de ejercicios sin contraindicaciones.
    :return: Prompt formateado para el modelo.
    """
    return f"""
Genera una rutina de ejercicios para un adulto mayor con el siguiente perfil:
- Edad: {profile.get('age')}
- Nivel: {profile.get('fitness_level')}
- Metas: {', '.join(profile.get('goals', []))}
- Restricciones médicas: {', '.join(profile.get('medical_restrictions', []))}
- Equipo disponible: {', '.join(profile.get('equipment', []))}

Ejercicios disponibles seguros: {[e['name'] for e in safe_exercises]}

Responde SOLO con JSON válido con la siguiente estructura:
{{
    "exercises": [{{"name": "string", "sets": int, "reps": int, "duration_min": int}}],
    "warmup": [{{"name": "string", "sets": int, "reps": int}}]
}}
"""


@app.post("/routines/generate")
async def generate_routine(req: GenerateRequest):
    """Genera una rutina de ejercicios para el día de hoy.

    Si ya existe una rutina activa para hoy y force=false, la retorna.
    Si Ollama falla, usa una rutina por defecto como fallback.

    :param req: Solicitud con user_id y flag force.
    :raises HTTPException 404: Si el usuario no existe.
    :return: Rutina generada con ID, ejercicios y warmup.
    """
    today = date.today()
    pool = await get_pool()

    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", req.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not req.force:
            existing = await conn.fetchrow(
                "SELECT id FROM routines WHERE user_id = $1 AND date = $2 AND active = true",
                req.user_id,
                today,
            )
            if existing:
                return {"detail": "Routine already exists for today", "routine_id": str(existing["id"])}

        profile = json.loads(user["profile"]) if isinstance(user["profile"], str) else (user["profile"] or {})
        exercises = await conn.fetch("SELECT * FROM exercises")
        safe_exercises = []
        restrictions = set(profile.get("medical_restrictions", []))
        for ex in exercises:
            ex_contra = set(ex.get("contraindications") or [])
            if not ex_contra.intersection(restrictions):
                safe_exercises.append(dict(ex))

    try:
        prompt = build_prompt(profile, safe_exercises)
        routine_data = await call_ollama(prompt)
    except Exception:
        routine_data = DEFAULT_ROUTINE

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO routines (user_id, date, exercises, warmup) VALUES ($1, $2, $3, $4) RETURNING id",
            req.user_id,
            today,
            json.dumps(routine_data.get("exercises", [])),
            json.dumps(routine_data.get("warmup", [])),
        )
        await publish_event("rutina-generada", {
            "user_id": req.user_id,
            "routine_id": str(row["id"]),
        })

    return {
        "routine_id": str(row["id"]),
        "exercises": routine_data.get("exercises", []),
        "warmup": routine_data.get("warmup", []),
    }


@app.get("/routines/today")
async def get_today_routine(user_id: str):
    """Obtiene la rutina activa del día de hoy para un usuario.

    :param user_id: ID del usuario.
    :raises HTTPException 404: Si no hay rutina para hoy.
    :return: Rutina del día con ejercicios y warmup.
    """
    today = date.today()
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM routines WHERE user_id = $1 AND date = $2 AND active = true",
            user_id,
            today,
        )
        if not row:
            raise HTTPException(status_code=404, detail="No routine for today")
        return {
            "id": str(row["id"]),
            "user_id": str(row["user_id"]),
            "date": row["date"].isoformat(),
            "exercises": row["exercises"],
            "warmup": row["warmup"],
        }
