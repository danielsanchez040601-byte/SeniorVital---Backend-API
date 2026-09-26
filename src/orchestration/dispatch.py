"""Dispatch Protocol — formato de mensajes y entry point del orquestador.

Define el contrato formal de comunicación entre el Orchestrator Agent y los
agentes especializados (S3-04):
- DispatchRequest: solicitud con request_id, intent, payload y context.
- DispatchResponse: respuesta estructurada con agente, safety y timing.
- Conversores bidireccionales con AgentMessage (protocolo existente).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.orchestration import AgentMessage
from src.orchestration.agent_protocol import AgentResponse, IntentResult


@dataclass
class DispatchRequest:
    """Solicitud de despacho hacia el Orchestrator Agent.

    Attributes:
        request_id: Identificador único de la solicitud (se genera si se omite).
        user_id: ID del usuario.
        message: Mensaje del usuario en texto plano.
        intent: Dominio de la intención (opcional — si no viene, el orquestador
                lo clasifica con IntentClassifier).
        payload: Datos adicionales de la solicitud (flexible).
        context: Contexto adicional (perfil, historial de herramientas, etc.).
        conversation_history: Historial reciente de la conversación.
        correlation_id: ID de correlación para trazabilidad.
    """

    request_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    user_id: int = 0
    message: str = ""
    intent: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    conversation_history: list[dict[str, Any]] = field(default_factory=list)
    correlation_id: str = ""

    def with_correlation(self, correlation_id: str) -> "DispatchRequest":
        """Retorna una copia con el correlation_id dado (para encadenar flujos)."""
        from copy import copy

        cloned = copy(self)
        cloned.correlation_id = correlation_id or self.correlation_id
        return cloned


@dataclass
class DispatchResponse:
    """Respuesta del despacho hacia el emisor.

    Attributes:
        request_id: Idéntico al de la solicitud.
        text: Respuesta textual para el usuario.
        agent: Nombre del agente que respondió.
        intent: Dominio clasificado (o el provisto en la solicitud).
        safety_level: Nivel de seguridad ("safe" | "warning" | "critical").
        tool_chain: Tools ejecutadas durante el procesamiento.
        blocked: True si la respuesta fue bloqueada por safety critical.
        duration_ms: Tiempo total del despacho en milisegundos.
        metadata: Metadatos adicionales del flujo.
    """

    request_id: str
    text: str
    agent: str = ""
    intent: str = ""
    safety_level: str = "safe"
    tool_chain: list[str] = field(default_factory=list)
    blocked: bool = False
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


def request_to_agent_message(request: DispatchRequest) -> AgentMessage:
    """Convierte DispatchRequest → AgentMessage (contrato wire del sistema).

    El AgentMessage conserva correlation_id/parent_id, y el payload viaja
    dentro de content con las llaves normalizadas que route() espera.
    """
    return AgentMessage(
        from_agent=request.context.get("from_agent", "user"),
        to_agent="orchestrator",
        content={
            "message": request.message,
            "user_id": request.user_id,
            "intent": request.intent,
            "user_profile": request.context.get("user_profile", {}),
            "conversation_history": request.conversation_history,
            "payload": request.payload,
        },
        message_type="query",
        correlation_id=request.correlation_id,
    )


def response_from_agent_message(message: AgentMessage) -> DispatchResponse:
    """Convierte AgentMessage (respuesta) → DispatchResponse."""
    content = message.content or {}
    return DispatchResponse(
        request_id=content.get("request_id", ""),
        text=content.get("response", ""),
        agent=content.get("agent", message.from_agent),
        intent=content.get("intent", ""),
        safety_level=content.get("safety_level", "safe"),
        tool_chain=content.get("tool_chain", []),
        blocked=content.get("blocked", False),
        metadata=content.get("metadata", {}),
    )


def intent_to_dispatch_intent(intent: IntentResult) -> str:
    """Normaliza un IntentResult a la llave intent de DispatchResponse."""
    return intent.domain


def response_to_dispatch_response(
    response: AgentResponse, *, request_id: str, agent: str, intent: str,
    duration_ms: float, blocked: bool = False, metadata: dict[str, Any] | None = None,
) -> DispatchResponse:
    """Convierte AgentResponse → DispatchResponse con metadata de flujo."""
    merged_metadata = dict(response.metadata or {})
    if metadata:
        merged_metadata.update(metadata)
    return DispatchResponse(
        request_id=request_id,
        text=response.text,
        agent=agent,
        intent=intent,
        safety_level=response.safety_level,
        tool_chain=response.tool_chain,
        blocked=blocked,
        duration_ms=round(duration_ms, 1),
        metadata=merged_metadata,
    )


def utc_now_iso() -> str:
    """Timestamp ISO-8601 UTC (helper para payloads de logs)."""
    return datetime.now(timezone.utc).isoformat()
