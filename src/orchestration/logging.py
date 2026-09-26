"""OrchestrationLogger — logging estructurado para trazabilidad de flujos.

Registra eventos de orquestación con correlation_id, timestamps, y timing
para permitir reconstruir el flujo completo de una solicitud.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any


logger = logging.getLogger(__name__)


class OrchestrationLogger:
    """Logger estructurado para el sistema de orquestación.

    Cada evento incluye:
    - timestamp: ISO-8601
    - correlation_id: ID de correlación del flujo
    - event: nombre del evento
    - data: payload del evento

    Precondiciones: None.
    Postcondiciones: Cada llamada genera un log event con estructura JSON.
    Efectos secundarios: Escribe logs vía logging estándar.
    """

    def _emit(self, event: str, correlation_id: str, data: dict[str, Any]) -> None:
        """Emite un evento de log estructurado."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id,
            "event": event,
            "data": data,
        }
        logger.info(json.dumps(entry, ensure_ascii=False, default=str))

    def route_start(
        self, correlation_id: str, user_id: int, message: str
    ) -> None:
        """Evento: inicio del routing de un mensaje."""
        self._emit("route_start", correlation_id, {
            "user_id": user_id,
            "message_preview": message[:100],
        })

    def intent_classified(
        self, correlation_id: str, domain: str, confidence: float, method: str = "llm"
    ) -> None:
        """Evento: intención clasificada."""
        self._emit("intent_classified", correlation_id, {
            "domain": domain,
            "confidence": round(confidence, 3),
            "method": method,
        })

    def agent_selected(self, correlation_id: str, agent_name: str) -> None:
        """Evento: agente seleccionado para procesar."""
        self._emit("agent_selected", correlation_id, {
            "agent": agent_name,
        })

    def delegation_start(
        self, correlation_id: str, from_agent: str, to_agent: str, parent_id: str = ""
    ) -> None:
        """Evento: inicio de delegación entre agentes."""
        self._emit("delegation_start", correlation_id, {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "parent_id": parent_id,
        })

    def delegation_end(
        self,
        correlation_id: str,
        from_agent: str,
        to_agent: str,
        duration_ms: float,
        success: bool,
        safety_level: str = "safe",
    ) -> None:
        """Evento: fin de delegación con timing y resultado."""
        self._emit("delegation_end", correlation_id, {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "duration_ms": round(duration_ms, 1),
            "success": success,
            "safety_level": safety_level,
        })

    def safety_check(
        self, correlation_id: str, agent_name: str, level: str, blocked: bool
    ) -> None:
        """Evento: validación de seguridad."""
        self._emit("safety_check", correlation_id, {
            "agent": agent_name,
            "level": level,
            "blocked": blocked,
        })

    def route_end(
        self, correlation_id: str, agent_name: str, duration_ms: float
    ) -> None:
        """Evento: fin del routing con timing."""
        self._emit("route_end", correlation_id, {
            "agent": agent_name,
            "duration_ms": round(duration_ms, 1),
        })

    def fallback_activated(
        self, correlation_id: str, reason: str, fallback_agent: str
    ) -> None:
        """Evento: activación del agente fallback."""
        self._emit("fallback_activated", correlation_id, {
            "reason": reason,
            "fallback_agent": fallback_agent,
        })

    def workflow_step(
        self,
        correlation_id: str,
        step_index: int,
        agent: str,
        skipped: bool = False,
    ) -> None:
        """Evento: paso de workflow ejecutado o saltado."""
        self._emit("workflow_step", correlation_id, {
            "step_index": step_index,
            "agent": agent,
            "skipped": skipped,
        })

    def dispatch_start(
        self, correlation_id: str, request_id: str, user_id: int, message: str,
        intent: str = "",
    ) -> None:
        """Evento: inicio de un despacho (S3-04 DispatchRequest)."""
        self._emit("dispatch_start", correlation_id, {
            "request_id": request_id,
            "user_id": user_id,
            "intent": intent,
            "message_preview": message[:100],
        })

    def dispatch_end(
        self, correlation_id: str, request_id: str, agent: str,
        duration_ms: float, safety_level: str = "safe", blocked: bool = False,
    ) -> None:
        """Evento: fin de un despacho con resultado y timing."""
        self._emit("dispatch_end", correlation_id, {
            "request_id": request_id,
            "agent": agent,
            "duration_ms": round(duration_ms, 1),
            "safety_level": safety_level,
            "blocked": blocked,
        })


def create_timer() -> tuple[callable]:
    """Crea un timer para medir duración de operaciones.

    Returns:
        Tupla con (elapsed_ms) que retorna milisegundos transcurridos.
    """
    start = time.monotonic()

    def elapsed_ms() -> float:
        return (time.monotonic() - start) * 1000

    return (elapsed_ms,)
