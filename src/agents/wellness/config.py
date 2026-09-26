"""Wellness Agent configuration."""

from dataclasses import dataclass, field
from typing import Any

from src.memory import MemoryStore
from src.tools import Tool


@dataclass
class WellnessConfig:
    """Configuración del Wellness Agent.

    Attributes:
        llm_url: URL base de Ollama (default: localhost:11434).
        llm_model: Modelo a usar (default: phi3:mini).
        llm_timeout: Timeout para llamadas LLM en segundos.
        db_url: URL de conexión a PostgreSQL (postgresql+asyncpg://...).
        max_react_iterations: Máximo de iteraciones del ciclo ReAct.
        conversation_history_limit: Número de mensajes recientes a incluir en prompts.
        tools: Herramientas inyectadas (vacío si no se proveen).
        memory_store: Backend de memoria conversacional (None si no disponible).
        user_profile_supplier: Callable async que retorna el perfil del usuario.
    """

    llm_url: str = "http://localhost:11434"
    llm_model: str = "phi3:mini"
    llm_timeout: float = 600.0
    db_url: str = ""

    # Coach Agent 2.0 fields
    max_react_iterations: int = 3
    tool_failure_threshold: int = 2  # Fallos consecutivos antes de abortar ciclo ReAct
    conversation_history_limit: int = 5
    tools: list[Tool] = field(default_factory=list)
    memory_store: MemoryStore | None = None
    user_profile_supplier: Any = None  # Callable[[int], dict] async
