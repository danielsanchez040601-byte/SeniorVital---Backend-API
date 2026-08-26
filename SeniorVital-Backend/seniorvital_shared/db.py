"""Gestión del pool de conexiones a PostgreSQL.

Mantiene un pool singleton con un sistema de propietario (owner)
para evitar cierres prematuros cuando múltiples servicios o tests
comparten la misma conexión.
"""

import asyncpg
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

_pool: Optional[asyncpg.Pool] = None
_pool_owner: Optional[str] = None


def _get_dsn():
    """Construye la cadena de conexión desde la variable de entorno DATABASE_URL.

    :return: DSN para conectar a PostgreSQL.
    """
    return os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:Nika@127.0.0.1:5432/senior_vital",
    )


async def init_pool(min_size=2, max_size=10, owner="default"):
    """Inicializa el pool de conexiones si aún no existe.

    :param min_size: Número mínimo de conexiones en el pool.
    :param max_size: Número máximo de conexiones en el pool.
    :param owner: Identificador del propietario para control de cierre.
    :return: El pool de conexiones de asyncpg.
    """
    global _pool, _pool_owner
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=_get_dsn(), min_size=min_size, max_size=max_size
        )
        _pool_owner = owner
    return _pool


async def close_pool(owner="default"):
    """Cierra el pool de conexiones si el propietario coincide.

    :param owner: Identificador del propietario. Solo cierra si coincide.
    """
    global _pool, _pool_owner
    if _pool is not None and _pool_owner == owner:
        await _pool.close()
        _pool = None
        _pool_owner = None


async def get_pool() -> asyncpg.Pool:
    """Retorna el pool de conexiones activo, inicializándolo si es necesario.

    :return: Pool de conexiones asyncpg.
    """
    if _pool is None:
        await init_pool()
    return _pool
