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
OLLAMA_MODEL = "phi3:mini"

DEFAULT_ROUTINE = {
    "exercises": [
        {"name": "Caminata ligera", "sets": 1, "reps": 10, "duration_min": 5},
        {"name": "Estiramiento de brazos", "sets": 2, "reps": 8, "duration_min": 3},
        {"name": "Respiración profunda", "sets": 1, "reps": 5, "duration_min": 2},
    ],
    "warmup": [{"name": "Rotación de cuello", "sets": 1, "reps": 5}],
}


class GenerateRequest(BaseModel):
    user_id: str
    force: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        )
        resp.raise_for_status()
        return json.loads(resp.json()["response"])


def build_prompt(profile: dict, safe_exercises: list) -> str:
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
