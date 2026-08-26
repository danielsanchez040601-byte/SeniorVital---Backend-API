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


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


async def call_ollama(prompt: str) -> dict:
    """Envía un prompt a Google AI Studio, OpenRouter o Ollama y parsea la respuesta JSON.

    :param prompt: Texto del prompt para el modelo.
    :raises httpx.HTTPError: Si la llamada al LLM falla.
    :return: Diccionario con la respuesta parseada.
    """
    # 1. Google AI Studio Directo (Gemini 3.6 Flash)
    if GEMINI_API_KEY:
        for gem_model in ["gemini-3.6-flash", "gemini-flash-latest"]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{gem_model}:generateContent?key={GEMINI_API_KEY}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"response_mime_type": "application/json"}
                }
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                        return json.loads(raw_text)
            except Exception as e:
                print(f"Aviso Google AI Studio ({gem_model}): {e}")

    # 2. OpenRouter
    if OPENROUTER_API_KEY:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://seniorvital-backend.onrender.com",
            "X-Title": "SeniorVital",
            "Content-Type": "application/json"
        }
        payload = {
            "model": DEFAULT_LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                if resp.status_code == 200:
                    content = resp.json()["choices"][0]["message"]["content"]
                    clean_json = content.strip()
                    if clean_json.startswith("```"):
                        clean_json = clean_json.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                    return json.loads(clean_json)
                else:
                    print(f"OpenRouter status {resp.status_code}: {resp.text}, usando fallback.")
        except Exception as e:
            print(f"Excepción en OpenRouter ({e}), usando fallback.")

    # 3. Fallback a Ollama local
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
