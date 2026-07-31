import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, timedelta
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from seniorvital_shared import get_pool, init_pool, close_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool(owner="dashboard")
    yield
    await close_pool(owner="dashboard")


app = FastAPI(
    title="Dashboard Service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
)


@app.get("/dashboard/progress/{user_id}")
async def get_progress(user_id: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT id FROM users WHERE id = $1", user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        week_ago = date.today() - timedelta(days=7)
        rows = await conn.fetch(
            """SELECT completed_at::date as day, SUM(reps) as total_reps,
                      AVG(rpe) as avg_rpe
               FROM tracking
               WHERE user_id = $1 AND completed_at >= $2
               GROUP BY completed_at::date
               ORDER BY day""",
            user_id,
            week_ago,
        )

        calendar = {}
        rpe_values = []
        for r in rows:
            day_str = r["day"].isoformat()
            calendar[day_str] = r["total_reps"]
            if r["avg_rpe"]:
                rpe_values.append(round(float(r["avg_rpe"]), 1))

        today = date.today()
        streak_days = 0
        check = today
        while True:
            day_rows = await conn.fetchval(
                "SELECT COUNT(*) FROM tracking WHERE user_id = $1 AND completed_at::date = $2",
                user_id,
                check,
            )
            if day_rows and day_rows > 0:
                streak_days += 1
                check -= timedelta(days=1)
            else:
                break

        total_sessions = await conn.fetchval(
            "SELECT COUNT(DISTINCT completed_at::date) FROM tracking WHERE user_id = $1 AND completed_at >= $2",
            user_id,
            week_ago,
        )

        return {
            "calendar": calendar,
            "avg_rpe_trend": rpe_values,
            "streak_days": streak_days,
            "total_sessions_week": total_sessions or 0,
        }


@app.get("/dashboard/projection/{user_id}")
async def get_projection(user_id: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM projections WHERE user_id = $1 ORDER BY week_start DESC LIMIT 1",
            user_id,
        )
        if not row:
            return {"projection": None}
        return {
            "projection": {
                "id": str(row["id"]),
                "week_start": row["week_start"].isoformat(),
                "insight_text": row["insight_text"],
                "estimated_level": row["estimated_level"],
            }
        }


@app.get("/dashboard/insights/{user_id}")
async def get_insights(user_id: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM projections WHERE user_id = $1 ORDER BY week_start DESC LIMIT 10",
            user_id,
        )
        return [
            {
                "id": str(r["id"]),
                "week_start": r["week_start"].isoformat(),
                "insight_text": r["insight_text"],
                "estimated_level": r["estimated_level"],
            }
            for r in rows
        ]
