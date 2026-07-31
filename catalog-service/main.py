import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import uuid
import aiofiles
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager

from seniorvital_shared import get_pool, init_pool, close_pool

MAX_VIDEO_SIZE = 50 * 1024 * 1024
STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "videos")
os.makedirs(STORAGE_DIR, exist_ok=True)


class ExerciseCreate(BaseModel):
    name: str
    level: int
    contraindications: List[str] = []
    video_url: Optional[str] = None


class ExerciseUpdate(BaseModel):
    name: Optional[str] = None
    level: Optional[int] = None
    contraindications: Optional[List[str]] = None
    video_url: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool(owner="catalog")
    yield
    await close_pool(owner="catalog")


app = FastAPI(
    title="Catalog Service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
)


@app.get("/catalog/exercises")
async def list_exercises(
    level: Optional[int] = Query(None, ge=1, le=4),
    name: Optional[str] = None,
):
    pool = await get_pool()
    async with pool.acquire() as conn:
        where = []
        params = []
        idx = 1
        if level is not None:
            where.append(f"level = ${idx}")
            params.append(level)
            idx += 1
        if name:
            where.append(f"name ILIKE ${idx}")
            params.append(f"%{name}%")
            idx += 1
        query = "SELECT * FROM exercises"
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY name"
        rows = await conn.fetch(query, *params)
        return [
            {
                "id": str(r["id"]),
                "name": r["name"],
                "level": r["level"],
                "contraindications": r.get("contraindications") or [],
                "video_url": r.get("video_url"),
            }
            for r in rows
        ]


@app.post("/catalog/exercises", status_code=201)
async def create_exercise(req: ExerciseCreate):
    if req.level < 1 or req.level > 4:
        raise HTTPException(status_code=400, detail="Level must be between 1 and 4")
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO exercises (name, level, contraindications, video_url) VALUES ($1, $2, $3, $4) RETURNING id",
            req.name,
            req.level,
            req.contraindications,
            req.video_url,
        )
    return {"id": str(row["id"]), "name": req.name}


@app.get("/catalog/exercises/{exercise_id}")
async def get_exercise(exercise_id: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM exercises WHERE id = $1", exercise_id)
        if not row:
            raise HTTPException(status_code=404, detail="Exercise not found")
        return {
            "id": str(row["id"]),
            "name": row["name"],
            "level": row["level"],
            "contraindications": row.get("contraindications") or [],
            "video_url": row.get("video_url"),
        }


@app.put("/catalog/exercises/{exercise_id}")
async def update_exercise(exercise_id: str, req: ExerciseUpdate):
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT * FROM exercises WHERE id = $1", exercise_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Exercise not found")
        updates = {}
        if req.name is not None:
            updates["name"] = req.name
        if req.level is not None:
            if req.level < 1 or req.level > 4:
                raise HTTPException(status_code=400, detail="Level must be between 1 and 4")
            updates["level"] = req.level
        if req.contraindications is not None:
            updates["contraindications"] = req.contraindications
        if req.video_url is not None:
            updates["video_url"] = req.video_url
        if updates:
            set_clause = ", ".join(f"{k} = ${i+1}" for i, k in enumerate(updates))
            values = list(updates.values()) + [exercise_id]
            await conn.execute(
                f"UPDATE exercises SET {set_clause} WHERE id = ${len(updates)+1}",
                *values,
            )
    return {"detail": "Exercise updated"}


@app.delete("/catalog/exercises/{exercise_id}")
async def delete_exercise(exercise_id: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM exercises WHERE id = $1", exercise_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Exercise not found")
    return {"detail": "Exercise deleted"}


@app.post("/catalog/exercises/{exercise_id}/video")
async def upload_video(exercise_id: str, file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")
    content = await file.read()
    if len(content) > MAX_VIDEO_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")
    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join(STORAGE_DIR, filename)
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)
    video_url = f"http://localhost:8002/storage/videos/{filename}"
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE exercises SET video_url = $1 WHERE id = $2", video_url, exercise_id)
    return {"video_url": video_url}


@app.get("/storage/videos/{filename}")
async def serve_video(filename: str):
    filepath = os.path.join(STORAGE_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(filepath, media_type="video/mp4")
