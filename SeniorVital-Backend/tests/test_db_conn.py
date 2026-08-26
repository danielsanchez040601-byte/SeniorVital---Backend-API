"""Script de verificación de conexión a PostgreSQL.

Conecta a la base de datos, imprime la versión y lista las tablas.
Útil para diagnóstico rápido de conectividad.
"""
import asyncio
import asyncpg


import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    """Conecta a PostgreSQL, imprime versión y lista de tablas."""
    dsn = os.getenv("DATABASE_URL", "postgresql://postgres:Nika@localhost:5432/senior_vital")
    conn = await asyncpg.connect(dsn)
    print("Connected!")
    ver = await conn.fetchval("SELECT version()")
    print(f"Version: {ver}")
    tables = await conn.fetch(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"
    )
    print("Tables:", [t["table_name"] for t in tables])
    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
