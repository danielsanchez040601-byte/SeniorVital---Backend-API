"""
Agente de Análisis Semanal: se ejecuta periódicamente (lunes a las 2 AM) para analizar 
el progreso, generar información utilizando Ollama y actualizar la tabla de proyecciones.
"""
import os
import sys
import json
import asyncio
import logging
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()

import asyncpg
import httpx
import duckdb
import uuid

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger("weekly_analysis")

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://sv_user:sv_pass@localhost:5432/seniorvital"
)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")


def _is_uuid(value: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False
DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "google/gemma-4-31b:free")
OLLAMA_MODEL = DEFAULT_LLM_MODEL
DUCKDB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "seniorvital_analytics.duckdb")


async def generate_insight(user_id: str, weekly_data: dict) -> dict:
    """Genera un insight usando Ollama a partir de datos semanales.

    :param user_id: ID del usuario analizado.
    :param weekly_data: Datos agregados de la semana.
    :return: Diccionario con insight_text y estimated_level.
    """
    prompt = f"""
Analiza el progreso semanal del usuario {user_id}:
- RPE promedio: {weekly_data.get('avg_rpe')}
- Total ejercicios: {weekly_data.get('total_exercises')}
- Racha (días): {weekly_data.get('streak_days')}

Genera un insight breve (máximo 2 oraciones) y un nivel estimado (1-4).
Responde SOLO con JSON: {{"insight_text": "...", "estimated_level": int}}
"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
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
    """Ejecuta el análisis semanal: lee DuckDB, llama Ollama y guarda en PostgreSQL."""
    pg_pool = await asyncpg.create_pool(dsn=DATABASE_URL, min_size=1, max_size=2)
    con = duckdb.connect(DUCKDB_PATH)
    try:
        rows = con.execute(
            "SELECT DISTINCT user_id FROM weekly_progress"
        ).fetchall()
        week_start = date.today() - timedelta(days=date.today().weekday())

        for (user_id,) in rows:
            try:
                # Skip non-UUID user_ids (test data)
                if not _is_uuid(user_id):
                    logger.warning(f"Skipping non-UUID user_id: {user_id}")
                    continue
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
            except Exception as e:
                logger.error(f"Weekly analysis failed for {user_id}: {e}")
    finally:
        con.close()
        await pg_pool.close()


async def main():
    """Punto de entrada: ejecuta el análisis semanal una vez."""
    logger.info("Weekly analysis started")
    await run_analysis()
    logger.info("Weekly analysis completed")


if __name__ == "__main__":
    asyncio.run(main())
