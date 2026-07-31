"""Test PostgreSQL connection."""
import asyncio
import asyncpg


async def main():
    conn = await asyncpg.connect(
        "postgresql://postgres:Nika@127.0.0.1:5432/seniorvital"
    )
    print("Connected!")
    ver = await conn.fetchval("SELECT version()")
    print(f"Version: {ver}")
    tables = await conn.fetch(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"
    )
    print("Tables:", [t["table_name"] for t in tables])
    await conn.close()


asyncio.run(main())
