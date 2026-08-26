"""
Replicador: lee eventos ejercicio-completado de PostgreSQL 
event_queue y los replica en DuckDB para análisis.
"""
import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()

import asyncpg
import duckdb

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger("replicator")

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://sv_user:sv_pass@localhost:5432/seniorvital"
)
DUCKDB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "seniorvital_analytics.duckdb")


async def ensure_duckdb_schema():
    """Crea las tablas raw_events y weekly_progress en DuckDB si no existen."""
    con = duckdb.connect(DUCKDB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS raw_events (
            event_id TEXT,
            user_id TEXT,
            event_type TEXT,
            payload JSON,
            ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS weekly_progress (
            user_id TEXT,
            week_start DATE,
            avg_rpe FLOAT,
            total_exercises INT,
            streak_days INT,
            projected_level INT
        )
    """)
    con.close()


async def process_events(pg_pool, duck_path):
    """Lee eventos no procesados de PostgreSQL y los replica en DuckDB.

    :param pg_pool: Pool de conexiones a PostgreSQL.
    :param duck_path: Ruta al archivo DuckDB.
    """
    try:
        con = duckdb.connect(duck_path)
        async with pg_pool.acquire() as pg_conn:
            rows = await pg_conn.fetch(
                """SELECT id, payload FROM event_queue
                    WHERE stream_name = 'ejercicio-completado' AND processed = FALSE
                    ORDER BY created_at LIMIT 100"""
            )
            for row in rows:
                event_id = str(row["id"])
                payload = json.loads(row["payload"]) if isinstance(row["payload"], str) else row["payload"]
                try:
                    con.execute(
                        "INSERT INTO raw_events (event_id, user_id, event_type, payload) VALUES (?, ?, ?, ?)",
                        [
                            event_id,
                            payload.get("user_id", ""),
                            "ejercicio-completado",
                            json.dumps(payload),
                        ],
                    )
                    user_id = payload.get("user_id", "")
                    rpe = payload.get("rpe")
                    week_start = datetime.now().date()
                    week_start = week_start - timedelta(days=week_start.weekday())
                    con.execute(
                        "DELETE FROM weekly_progress WHERE user_id = ? AND week_start = ?",
                        [user_id, week_start.isoformat()],
                    )
                    con.execute("""
                        INSERT INTO weekly_progress (user_id, week_start, avg_rpe, total_exercises, streak_days, projected_level)
                        VALUES (?, ?, ?, ?, 0, NULL)
                    """, [user_id, week_start.isoformat(), float(rpe) if rpe else None, 1])

                    await pg_conn.execute(
                        "UPDATE event_queue SET processed = TRUE, processed_at = NOW() WHERE id = $1",
                        row["id"],
                    )
                    logger.info(f"Replicated event {event_id}")
                except Exception as e:
                    logger.error(f"Failed to replicate event {event_id}: {e}")
        con.close()
    except Exception as e:
        logger.error(f"Error in replication cycle: {e}")


async def main():
    """Bucle principal del replicador: schema, pool y polling infinito."""
    logger.info("Replicator started")
    await ensure_duckdb_schema()
    pg_pool = await asyncpg.create_pool(dsn=DATABASE_URL, min_size=1, max_size=2)
    try:
        while True:
            await process_events(pg_pool, DUCKDB_PATH)
            await asyncio.sleep(1)
    finally:
        await pg_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
