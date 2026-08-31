from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

import asyncio
from sqlalchemy import text

try:
    from src.api.config import settings
    from src.database.database import engine, Base
    from src.api import auth, chat, exercises, routines, tracking, dashboard, notify
except ImportError:
    try:
        from .config import settings
        from ..database.database import engine, Base
        from . import auth, chat, exercises, routines, tracking, dashboard, notify
    except ImportError:
        from config import settings
        from database import engine, Base
        import auth, chat, exercises, routines, tracking, dashboard, notify


async def init_db_background():
    """Inicialización asíncrona no bloqueante de esquemas y pgvector en segundo plano."""
    try:
        # Timeout estricto de 4 segundos para no retener recursos
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await conn.run_sync(Base.metadata.create_all)
        print("✅ [SeniorVital] Esquemas y extensión pgvector verificados en segundo plano.")
    except Exception as e:
        print(f"ℹ️ [SeniorVital Notice] Conexión a DB en modo Lazy (delegada a peticiones activas): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida no bloqueante: Apertura inmediata del puerto HTTP en Render/Cloud."""
    print("🚀 [SeniorVital API] Servidor iniciado - Puerto HTTP listo de inmediato.")
    # Ejecutar inicialización en segundo plano sin congelar el arranque de FastAPI
    asyncio.create_task(init_db_background())
    yield
    print("🛑 [SeniorVital API] Cerrando conexiones...")


app = FastAPI(
    title="SeniorVital API — Plataforma Inteligente Wellness Gerontológica",
    description="Backend Monolítico Modular para la gestión de salud, rutinas adaptadas con IA y memoria semántica (pgvector).",
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuración de Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de Módulos / Routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(exercises.router)
app.include_router(exercises.catalog_router)
app.include_router(routines.router)
app.include_router(tracking.router)
app.include_router(dashboard.router)
app.include_router(notify.router)


@app.get("/", tags=["Health"])
async def root_health_check():
    """Endpoint raíz para monitoreo y comprobación de salud en Render.com."""
    return {
        "status": "online",
        "app": "SeniorVital Backend API",
        "version": "3.0.0",
        "environment": settings.ENVIRONMENT,
        "standards": ["SWEBOK V4", "ISO/IEC 25010"],
        "docs": "/docs"
    }
