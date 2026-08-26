"""Configuración compartida de pytest para SeniorVital.

Inicializa el pool de base de datos, proporciona la función
load_service_app para cargar dinámicamente cada microservicio
y limpia los datos entre ejecuciones de tests.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import importlib.util
import pytest
from dotenv import load_dotenv
from seniorvital_shared import init_pool, close_pool, get_pool

load_dotenv()

os.environ["DATABASE_URL"] = os.getenv("DATABASE_URL", "postgresql://postgres:Nika@localhost:5432/senior_vital")


def load_service_app(service_name: str):
    """Carga dinámicamente la aplicación FastAPI de un microservicio.

    :param service_name: Nombre del directorio del servicio (ej. 'auth-profile-service').
    :return: Instancia de la aplicación FastAPI.
    """
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), service_name, "main.py")
    spec = importlib.util.spec_from_file_location(service_name.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), service_name))
    spec.loader.exec_module(mod)
    return mod.app


@pytest.fixture(autouse=True)
async def auto_init_pool():
    """Fixture que inicializa el pool de BD antes de cada test y lo cierra al finalizar."""
    await init_pool(min_size=1, max_size=5, owner="test")
    yield
    await close_pool(owner="test")


@pytest.fixture(autouse=True)
async def cleanup():
    """Fixture que limpia todas las tablas después de cada test."""
    yield
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM event_queue")
        await conn.execute("DELETE FROM tracking")
        await conn.execute("DELETE FROM routines")
        await conn.execute("DELETE FROM projections")
        await conn.execute("DELETE FROM push_subscriptions")
        await conn.execute("DELETE FROM exercises")
        await conn.execute("DELETE FROM habits")
        await conn.execute("DELETE FROM users")
