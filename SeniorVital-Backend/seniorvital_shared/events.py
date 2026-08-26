"""Publicación de eventos asíncronos en la tabla event_queue.

Cada evento se inserta en PostgreSQL con un stream_name que identifica
el tipo de evento y un payload JSON con los datos asociados.
"""

import json
import asyncpg
from .db import get_pool


async def publish_event(stream_name: str, payload: dict) -> None:
    """Inserta un evento en la cola de eventos asíncronos.

    :param stream_name: Identificador del tipo de evento
        (ej. 'ejercicio-completado', 'fatiga-alta').
    :param payload: Diccionario con los datos del evento.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO event_queue (stream_name, payload) VALUES ($1, $2)",
            stream_name,
            json.dumps(payload),
        )
