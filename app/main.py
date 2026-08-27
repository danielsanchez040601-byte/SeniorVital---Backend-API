from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from sqlalchemy import text
from .config import settings
from .database import engine, Base
from .routers import auth, chat, exercises, routines, tracking, dashboard, notify


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicialización y limpieza del ciclo de vida de la aplicación."""
    print("🚀 [SeniorVital] Inicializando tablas y esquemas en PostgreSQL / Supabase con pgvector...")
    try:
        async with engine.begin() as conn:
            # 1. Habilitar extensión vectorial pgvector si no existe
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            # 2. Sincronizar modelos relacionales
            await conn.run_sync(Base.metadata.create_all)
        print("✅ [SeniorVital] Conexión a Base de Datos y extensión pgvector establecidas.")
    except Exception as e:
        print(f"⚠️ [SeniorVital Warning] Inicialización de DB en modo resiliente: {e}")
    yield
    print("🛑 [SeniorVital] Cerrando conexiones...")


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
