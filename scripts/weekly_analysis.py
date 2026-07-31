"""
Weekly Analysis Agent: runs periodically (Mondays 2 AM) to analyze progress,
generate insights using Ollama, and update projections table.
"""
import os
import sys
import json
import asyncio
import logging
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import asyncpg
import httpx
import duckdb

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger("weekly_analysis")

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://sv_user:sv_pass@localhost:5432/seniorvital"
)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = "phi3:mini"
DUCKDB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "seniorvital_analytics.duckdb")


async def generate_insight(user_id: str, weekly_data: dict) -> dict:
    prompt = f"""
Analiza el progreso semanal del usuario {user_id}:
- RPE promedio: {weekly_data.get('avg_rpe')}
- Total ejercicios: {weekly_data.get('total_exercises')}
- Racha (días): {weekly_data.get('streak_days')}

Genera un insight breve (máximo 2 oraciones) y un nivel estimado (1-4).
Responde SOLO con JSON: {{"insight_text": "...", "estimated_level": int}}
"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            )
            resp.raise_for_status()
            return json.loads(resp.json()["response"])
    except Exception as e:
        logger.error(f"Ollama insight failed for {user_id}: {e}")
        return {"insight_text": "Sin datos suficientes para generar insight.", "estimated_level": 1}


async def run_analysis():
    pg_pool = await asyncpg.create_pool(dsn=DATABASE_URL, min_size=1, max_size=2)
    con = duckdb.connect(DUCKDB_PATH)
    try:
        rows = con.execute(
            "SELECT DISTINCT user_id FROM weekly_progress"
        ).fetchall()
        week_start = date.today() - timedelta(days=date.today().weekday())

        for (user_id,) in rows:
            weekly = con.execute(
                """SELECT AVG(avg_rpe) as avg_rpe, SUM(total_exercises) as total_exercises,
                          MAX(streak_days) as streak_days
                   FROM weekly_progress
                   WHERE user_id = ? AND week_start = ?""",
                [user_id, week_start.isoformat()],
            ).fetchone()

            if weekly and weekly[0]:
                insight = await generate_insight(user_id, {
                    "avg_rpe": weekly[0],
                    "total_exercises": weekly[1] or 0,
                    "streak_days": weekly[2] or 0,
                })
                async with pg_pool.acquire() as pg_conn:
                    await pg_conn.execute(
                        "INSERT INTO projections (user_id, week_start, insight_text, estimated_level) VALUES ($1, $2, $3, $4)",
                        user_id,
                        week_start,
                        insight.get("insight_text", ""),
                        insight.get("estimated_level", 1),
                    )
                    await pg_conn.execute(
                        "INSERT INTO event_queue (stream_name, payload) VALUES ($1, $2)",
                        "recomendacion-ajuste",
                        json.dumps({
                            "user_id": user_id,
                            "week_start": week_start.isoformat(),
                            "insight": insight.get("insight_text", ""),
                        }),
                    )
                    logger.info(f"Weekly analysis done for {user_id}")
    finally:
        con.close()
        await pg_pool.close()


async def main():
    logger.info("Weekly analysis started")
    await run_analysis()
    logger.info("Weekly analysis completed")


if __name__ == "__main__":
    asyncio.run(main())
