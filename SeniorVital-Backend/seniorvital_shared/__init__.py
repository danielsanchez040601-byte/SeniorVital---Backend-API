"""Librería compartida del ecosistema SeniorVital.

Proporciona componentes reutilizables para todos los microservicios:
gestión del pool de conexiones a PostgreSQL, modelos de dominio
validados con Pydantic y publicación de eventos asíncronos.
"""

from .db import get_pool, init_pool, close_pool
from .models import HealthProfile
from .events import publish_event

__all__ = ["get_pool", "init_pool", "close_pool", "HealthProfile", "publish_event"]
