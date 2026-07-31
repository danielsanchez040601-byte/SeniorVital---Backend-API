import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
from datetime import datetime, date as date_type
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager

from seniorvital_shared import get_pool, init_pool, close_pool


class TrackEntry(BaseModel):
    user_id: str
    exercise_id: str
    sets: int
    reps: int
    rpe: Optional[int] = None
    felt_difficulty: Optional[str] = None
    completed_at: Optional[datetime] = None


class BatchTrackRequest(BaseModel):
    entries: List[TrackEntry]


@asynccontextmanager
async def lifespan(app: FastAPI):
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


class HabitUpdate(BaseModel):
    user_id: str
    date: Optional[date_type] = None
    water_glasses: Optional[int] = None
    walking_minutes: Optional[int] = None
    meds_taken: Optional[bool] = None


@app.get("/tracking/habits")
async def get_habits(user_id: str, date: Optional[date_type] = None):
    target_date = date or date_type.today()
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM habits WHERE user_id = $1 AND date = $2",
            user_id,
            target_date,
        )
        if not row:
            return {
                "user_id": user_id,
                "date": target_date.isoformat(),
                "water_glasses": 0,
                "walking_minutes": 0,
                "meds_taken": False,
            }
        return {
            "id": str(row["id"]),
            "user_id": str(row["user_id"]),
            "date": row["date"].isoformat(),
            "water_glasses": row["water_glasses"] or 0,
            "walking_minutes": row["walking_minutes"] or 0,
            "meds_taken": row["meds_taken"] or False,
        }


@app.post("/tracking/habits")
async def update_habits(req: HabitUpdate):
    target_date = req.date or date_type.today()
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT * FROM habits WHERE user_id = $1 AND date = $2",
            req.user_id,
            target_date,
        )
        if existing:
            water = req.water_glasses if req.water_glasses is not None else (existing["water_glasses"] or 0)
            walking = req.walking_minutes if req.walking_minutes is not None else (existing["walking_minutes"] or 0)
            meds = req.meds_taken if req.meds_taken is not None else (existing["meds_taken"] or False)
            await conn.execute(
                """UPDATE habits 
                   SET water_glasses = $1, walking_minutes = $2, meds_taken = $3 
                   WHERE user_id = $4 AND date = $5""",
                water,
                walking,
                meds,
                req.user_id,
                target_date,
            )
        else:
            water = req.water_glasses if req.water_glasses is not None else 0
            walking = req.walking_minutes if req.walking_minutes is not None else 0
            meds = req.meds_taken if req.meds_taken is not None else False
            await conn.execute(
                """INSERT INTO habits (user_id, date, water_glasses, walking_minutes, meds_taken)
                   VALUES ($1, $2, $3, $4, $5)""",
                req.user_id,
                target_date,
                water,
                walking,
                meds,
            )
    return {"detail": "Habits updated"}
