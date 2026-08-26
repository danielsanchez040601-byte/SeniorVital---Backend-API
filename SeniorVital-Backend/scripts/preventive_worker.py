"""
Trabajador Preventivo: consume eventos de fatiga-alta de la cola_de_eventos
y realiza acciones preventivas (registro, notificaciones, etc.)
"""
import os
import sys
import json
import asyncio
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()

import asyncpg
import httpx

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger("preventive_worker")

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://sv_user:sv_pass@localhost:5432/seniorvital"
)


async def process_events(pg_pool):
    """Procesa eventos de fatiga-alta no procesados.

    Para cada evento, loggea una advertencia e intenta notificar
    al usuario a través del servicio de notificaciones.

    :param pg_pool: Pool de conexiones a PostgreSQL.
    """
    try:
        async with pg_pool.acquire() as pg_conn:
            rows = await pg_conn.fetch(
                """SELECT id, payload FROM event_queue
                    WHERE stream_name = 'fatiga-alta' AND processed = FALSE
                    ORDER BY created_at LIMIT 50"""
            )
            for row in rows:
                event_id = str(row["id"])
                payload = row["payload"]
                try:
                    parsed = json.loads(payload) if isinstance(payload, str) else payload
                    user_id = parsed.get("user_id")
                    rpe_value = parsed.get("rpe_value")
                    logger.warning(
                        f"High fatigue detected: user={user_id}, rpe={rpe_value}"
                    )
                    try:
                        async with httpx.AsyncClient(timeout=5.0) as client:
                            await client.post(
                                f"http://localhost:8006/notify/send",
                                json={
                                    "user_id": user_id,
                                    "title": "Fatiga alta detectada",
                                    "body": f"Se detectó fatiga alta (RPE: {rpe_value}). Considere reducir intensidad.",
                                },
                            )
                    except Exception:
                        pass
                    await pg_conn.execute(
                        "UPDATE event_queue SET processed = TRUE, processed_at = NOW() WHERE id = $1",
                        row["id"],
                    )
                    logger.info(f"Processed fatiga-alta event {event_id}")
                except Exception as e:
                    logger.error(f"Failed to process event {event_id}: {e}")
    except Exception as e:
        logger.error(f"Error in preventive worker cycle: {e}")


async def main():
    """Bucle principal del worker preventivo: pool y polling infinito."""
    logger.info("Preventive worker started")
    pg_pool = await asyncpg.create_pool(dsn=DATABASE_URL, min_size=1, max_size=2)
    try:
        while True:
            await process_events(pg_pool)
            await asyncio.sleep(2)
    finally:
        await pg_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
