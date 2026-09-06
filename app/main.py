"""
Proxy de compatibilidad para Render / despliegues en producción.
Redirige la aplicación FastAPI a src.api.main:app.
"""
from src.api.main import app

__all__ = ["app"]
