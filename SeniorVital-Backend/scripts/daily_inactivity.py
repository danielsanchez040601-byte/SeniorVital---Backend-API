"""
Agente de Inactividad Diaria: verifica a los usuarios que han estado inactivos
durante más de 4 días y publica eventos inactividad-detectada en event_queue.
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

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger("daily_inactivity")

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://sv_user:sv_pass@localhost:5432/seniorvital"
)


async def check_inactivity():
    """Detecta seniors inactivos (sin tracking en 4+ días) y publica eventos.

    Por cada usuario inactivo, inserta un evento inactividad-detectada
    en la cola de eventos de PostgreSQL.
    """
    pg_pool = await asyncpg.create_pool(dsn=DATABASE_URL, min_size=1, max_size=2)
    try:
        async with pg_pool.acquire() as conn:
            four_days_ago = date.today() - timedelta(days=4)
            rows = await conn.fetch(
                """SELECT id as user_id FROM users WHERE role = 'senior'
                   AND id NOT IN (
                       SELECT user_id FROM tracking
                       WHERE completed_at::date >= $1
                   )""",
                four_days_ago,
            )
            for row in rows:
                user_id = str(row["user_id"])
                days_inactive = 4
                await conn.execute(
                    "INSERT INTO event_queue (stream_name, payload) VALUES ($1, $2)",
                    "inactividad-detectada",
                    json.dumps({
                        "user_id": user_id,
                        "days_inactive": days_inactive,
                    }),
                )
                logger.info(f"Inactivity detected for user {user_id}")
    finally:
        await pg_pool.close()


async def main():
    """Punto de entrada: ejecuta la detección de inactividad una vez."""
    logger.info("Daily inactivity check started")
    await check_inactivity()
    logger.info("Daily inactivity check completed")


if __name__ == "__main__":
    asyncio.run(main())
