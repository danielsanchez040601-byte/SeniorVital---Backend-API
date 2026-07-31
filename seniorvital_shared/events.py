import json
import asyncpg
from .db import get_pool


async def publish_event(stream_name: str, payload: dict) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO event_queue (stream_name, payload) VALUES ($1, $2)",
            stream_name,
            json.dumps(payload),
        )
