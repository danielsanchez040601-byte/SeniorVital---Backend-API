"""Agent Protocol — interfaces base para el sistema multiagente.

Define los contratos de comunicación entre agentes, incluyendo
solicitudes, respuestas, y el Protocol que todos los agentes deben implementar.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class AgentRequest:
    """Solicitud entrante a un agente.

    Attributes:
        message: Mensaje del usuario en texto plano.
        user_id: ID numérico del usuario.
        user_profile: Perfil del usuario (name, age, health, preferences).
        conversation_history: Historial reciente de la conversación.
        context: Contexto adicional flexible (tool results, metadata).
    """

    message: str
    user_id: int
    user_profile: dict[str, Any] = field(default_factory=dict)
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResponse:
    """Respuesta saliente de un agente.

    Attributes:
        text: Respuesta textual para el usuario.
        safety_level: Nivel de seguridad detectado ("safe" | "warning" | "critical").
        tool_chain: Lista de tools ejecutadas durante el procesamiento.
        metadata: Metadatos adicionales (latencia, tokens, etc.).
    """

    text: str
    safety_level: str = "safe"
    tool_chain: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IntentResult:
    """Resultado de la clasificación de intención.

    Attributes:
        domain: Dominio detectado (e.g., "nutrition", "analytics", "general").
        confidence: Confianza de la clasificación en [0.0, 1.0].
        keywords: Keywords que triggeron la clasificación.
        raw_llm_response: Respuesta cruda del LLM para debug.
    """

    domain: str
    confidence: float
    keywords: list[str] = field(default_factory=list)
    raw_llm_response: str = ""


@runtime_checkable
class Agent(Protocol):
    """Contrato base para todos los agentes del sistema multiagente.

    Precondiciones:
        - El agente está inicializado con sus dependencias (LLM, tools, etc.).
        - El LLM está disponible y respondiendo.

    Postcondiciones:
        - handle() retorna un AgentResponse con safety_level válido.
        - can_handle() retorna True/False sin efectos secundarios.

    Efectos secundarios:
        - handle() puede ejecutar tools que modifican BD.
        - handle() puede persistir mensajes en memoria.
        - Cada implementación documenta sus efectos colaterales.
    """

    name: str
    domain: str
    description: str

    async def handle(self, request: AgentRequest) -> AgentResponse:
        """Procesa una solicitud del usuario y retorna una respuesta.

        Args:
            request: Solicitud con mensaje, perfil y contexto del usuario.

        Returns:
            AgentResponse con respuesta textual y nivel de seguridad.
        """
        ...

    def can_handle(self, intent: str, confidence: float) -> bool:
        """Determina si este agente puede manejar la intención dada.

        Args:
            intent: Dominio de intención clasificado.
            confidence: Confianza de la clasificación.

        Returns:
            True si el agente puede manejar la intención.
        """
        ...
