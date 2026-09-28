import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

try:
    from src.api.config import settings
except ImportError:
    try:
        from ..api.config import settings
    except ImportError:
        from config import settings

# Formatear URL para el driver asíncrono asyncpg y conexión a Supabase
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Crear motor asíncrono con pool defensivo optimizado para Supabase (puerto 6543 / Pooler)
connect_args = {}
if "6543" in db_url or "pooler.supabase.com" in db_url:
    connect_args = {
        "prepared_statement_cache_size": 0,
        "statement_cache_size": 0
    }

engine = create_async_engine(
    db_url,
    echo=False,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
    connect_args=connect_args
)

# Fábrica de sesiones asíncronas
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()


async def get_db():
    """Generador de dependencias de sesión asíncrona de base de datos."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
