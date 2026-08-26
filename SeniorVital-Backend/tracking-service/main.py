"""Microservicio de tracking de ejercicios.

Registra sesiones de ejercicio, publica eventos de completado
y detecta fatiga alta para activar alertas preventivas.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()

import json
from datetime import datetime, date
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager

from seniorvital_shared import get_pool, init_pool, close_pool


class TrackEntry(BaseModel):
    """Datos de una entrada individual de tracking de ejercicio."""
    user_id: str
    exercise_id: str
    sets: int
    reps: int
    rpe: Optional[int] = None
    felt_difficulty: Optional[str] = None
    completed_at: Optional[datetime] = None


class BatchTrackRequest(BaseModel):
    """Solicitud para registrar múltiples entradas de tracking."""
    entries: List[TrackEntry]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida del servicio: inicializa y cierra el pool de conexiones."""
    await init_pool(owner="tracking")
    yield
    await close_pool(owner="tracking")


app = FastAPI(
    title="Tracking Service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
)


@app.post("/tracking/record")
async def record_exercise(entry: TrackEntry):
    """Registra un ejercicio completado y publica eventos asociados.

    Si el RPE es >= 8, publica además un evento de fatiga-alta.
    Todo se ejecuta dentro de una misma transacción.

    :param entry: Datos del ejercicio registrado.
    :return: ID del registro y confirmación.
    """
    pool = await get_pool()
    completed_at = entry.completed_at or datetime.utcnow()
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """INSERT INTO tracking (user_id, exercise_id, sets, reps, rpe, felt_difficulty, completed_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id""",
                entry.user_id,
                entry.exercise_id,
                entry.sets,
                entry.reps,
                entry.rpe,
                entry.felt_difficulty,
                completed_at,
            )
            event_payload = {
                "user_id": entry.user_id,
                "exercise_id": entry.exercise_id,
                "rpe": entry.rpe,
                "timestamp": completed_at.isoformat(),
                "sets": entry.sets,
                "reps": entry.reps,
            }
            await conn.execute(
                "INSERT INTO event_queue (stream_name, payload) VALUES ($1, $2)",
                "ejercicio-completado",
                json.dumps(event_payload),
            )
            if entry.rpe is not None and entry.rpe >= 8:
                await conn.execute(
                    "INSERT INTO event_queue (stream_name, payload) VALUES ($1, $2)",
                    "fatiga-alta",
                    json.dumps({
                        "user_id": entry.user_id,
                        "rpe_value": entry.rpe,
                        "exercise_id": entry.exercise_id,
                    }),
                )
    return {"id": str(row["id"]), "detail": "Exercise recorded"}


@app.post("/tracking/batch")
async def record_batch(req: BatchTrackRequest):
    """Registra un lote de ejercicios en una sola transacción.

    :param req: Lista de entradas de tracking.
    :return: IDs de los registros creados y conteo total.
    """
    pool = await get_pool()
    ids = []
    async with pool.acquire() as conn:
        async with conn.transaction():
            for entry in req.entries:
                completed_at = entry.completed_at or datetime.utcnow()
                row = await conn.fetchrow(
                    """INSERT INTO tracking (user_id, exercise_id, sets, reps, rpe, felt_difficulty, completed_at)
                       VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id""",
                    entry.user_id,
                    entry.exercise_id,
                    entry.sets,
                    entry.reps,
                    entry.rpe,
                    entry.felt_difficulty,
                    completed_at,
                )
                ids.append(str(row["id"]))
                event_payload = {
                    "user_id": entry.user_id,
                    "exercise_id": entry.exercise_id,
                    "rpe": entry.rpe,
                    "timestamp": completed_at.isoformat(),
                    "sets": entry.sets,
                    "reps": entry.reps,
                }
                await conn.execute(
                    "INSERT INTO event_queue (stream_name, payload) VALUES ($1, $2)",
                    "ejercicio-completado",
                    json.dumps(event_payload),
                )
                if entry.rpe is not None and entry.rpe >= 8:
                    await conn.execute(
                        "INSERT INTO event_queue (stream_name, payload) VALUES ($1, $2)",
                        "fatiga-alta",
                        json.dumps({
                            "user_id": entry.user_id,
                            "rpe_value": entry.rpe,
                            "exercise_id": entry.exercise_id,
                        }),
                    )
    return {"ids": ids, "count": len(ids)}


class HabitEntry(BaseModel):
    """Datos de una entrada de hábito diario."""
    user_id: str
    date: date
    water_glasses: Optional[int] = None
    sleep_hours: Optional[float] = None
    walking_minutes: Optional[int] = None
    meds_taken: Optional[bool] = None


@app.post("/tracking/habits")
async def record_habit(entry: HabitEntry):
    """Registra o actualiza los hábitos de un día para un usuario."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO habits (user_id, date, water_glasses, sleep_hours, walking_minutes, meds_taken)
               VALUES ($1, $2, $3, $4, $5, $6)
               ON CONFLICT (user_id, date) DO UPDATE 
               SET water_glasses = COALESCE(EXCLUDED.water_glasses, habits.water_glasses),
                   sleep_hours = COALESCE(EXCLUDED.sleep_hours, habits.sleep_hours),
                   walking_minutes = COALESCE(EXCLUDED.walking_minutes, habits.walking_minutes),
                   meds_taken = COALESCE(EXCLUDED.meds_taken, habits.meds_taken)""",
            entry.user_id,
            entry.date,
            entry.water_glasses,
            entry.sleep_hours,
            entry.walking_minutes,
            entry.meds_taken,
        )
    return {"detail": "Habit recorded/updated"}


@app.get("/tracking/habits/{user_id}/{date_str}")
async def get_habit_for_date(user_id: str, date_str: str):
    """Obtiene los hábitos de un usuario para una fecha específica."""
    try:
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format, use YYYY-MM-DD")
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM habits WHERE user_id = $1 AND date = $2",
            user_id,
            parsed_date,
        )
        if not row:
            return {
                "user_id": user_id,
                "date": date_str,
                "water_glasses": 0,
                "sleep_hours": 0.0,
                "walking_minutes": 0,
                "meds_taken": None
            }
        return {
            "id": str(row["id"]),
            "user_id": str(row["user_id"]),
            "date": row["date"].isoformat(),
            "water_glasses": row["water_glasses"] or 0,
            "sleep_hours": row["sleep_hours"] or 0.0,
            "walking_minutes": row["walking_minutes"] or 0,
            "meds_taken": row["meds_taken"]
        }


@app.get("/tracking/habits/{user_id}")
async def get_habits_history(user_id: str):
    """Obtiene todo el historial de hábitos de un usuario."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM habits WHERE user_id = $1 ORDER BY date DESC",
            user_id,
        )
        return [
            {
                "id": str(r["id"]),
                "user_id": str(r["user_id"]),
                "date": r["date"].isoformat(),
                "water_glasses": r["water_glasses"] or 0,
                "sleep_hours": r["sleep_hours"] or 0.0,
                "walking_minutes": r["walking_minutes"] or 0,
                "meds_taken": r["meds_taken"]
            }
            for r in rows
        ]

