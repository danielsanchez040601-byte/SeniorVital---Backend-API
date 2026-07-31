import asyncpg
import os
from typing import Optional
from dotenv import load_dotenv

shared_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(shared_dir)
env_path = os.path.join(backend_dir, ".env")
load_dotenv(env_path)

_pool: Optional[asyncpg.Pool] = None
_pool_owner: Optional[str] = None


def _get_dsn():
    return os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:Nika@127.0.0.1:5432/seniorvital",
    )


async def init_pool(min_size=2, max_size=10, owner="default"):
    global _pool, _pool_owner
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=_get_dsn(), min_size=min_size, max_size=max_size
        )
        _pool_owner = owner
    return _pool


async def close_pool(owner="default"):
    global _pool, _pool_owner
    if _pool is not None and _pool_owner == owner:
        await _pool.close()
        _pool = None
        _pool_owner = None


async def get_pool() -> asyncpg.Pool:
    if _pool is None:
        await init_pool()
    return _pool
