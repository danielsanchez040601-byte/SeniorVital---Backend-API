"""Orchestration module — protocols para orquestación de agentes.

Este módulo define las interfaces (protocols) para orquestadores de agentes
y comunicación inter-agente. Las implementaciones concretas se crearán en S2-05.

Ejemplo de uso::

    from src.orchestration import Orchestrator, AgentMessage

    class SimpleOrchestrator:
        async def route(self, message: AgentMessage) -> AgentMessage:
            return AgentMessage(
                from_agent=message.to_agent,
                to_agent=message.from_agent,
                content={"response": "OK"},
                message_type="response",
                correlation_id=message.correlation_id,
            )

        async def delegate(self, from_agent: str, to_agent: str, task: dict) -> dict:
            return {"status": "delegated"}
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable
import uuid


@dataclass
class AgentMessage:
    """Mensaje inter-agente en el sistema multi-agente.

    Attributes:
        from_agent: Nombre del agente emisor.
        to_agent: Nombre del agente receptor.
        content: Contenido del mensaje (dict flexible).
        message_type: Tipo de mensaje. Valores válidos: "query", "response",
                      "delegation", "alert".
        correlation_id: ID de correlación para trazar el flujo entre agentes.
                        Se genera automáticamente si no se proporciona.
        parent_id: ID de correlación del mensaje padre (para delegaciones anidadas).
        timestamp: Timestamp ISO-8601 del mensaje.
    """

    from_agent: str
    to_agent: str
    content: dict
    message_type: str  # "query" | "response" | "delegation" | "alert"
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    parent_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class OrchestrationError(Exception):
    """Se lanza cuando la orquestación falla de forma irrecuperable.

    Attributes:
        source_agent: Agente que originó el error.
        target_agent: Agente destino (None si es error de routing).
    """

    def __init__(self, message: str, source_agent: str = "", target_agent: str = "") -> None:
        super().__init__(message)
        self.source_agent = source_agent
        self.target_agent = target_agent


class AgentNotFoundError(Exception):
    """Se lanza cuando se intenta enrutar un mensaje a un agente que no existe.

    Attributes:
        agent_name: Nombre del agente no encontrado.
    """

    def __init__(self, agent_name: str) -> None:
        super().__init__(f"Agent not found: {agent_name}")
        self.agent_name = agent_name


@runtime_checkable
class Orchestrator(Protocol):
    """Contrato para orquestadores de agentes.

    Precondiciones:
        - Todos los agentes registrados deben estar inicializados.
        - El orquestador tiene acceso al registro de agentes disponibles.

    Postcondiciones:
        - route() retorna un AgentMessage con la respuesta del agente destino.
        - delegate() retorna el resultado de la tarea delegada.
        - Las operaciones son atómicas — falla completa si hay error.

    Efectos secundarios:
        - Puede enviar mensajes a otros agentes.
        - Puede ejecutar herramientas vía Tool Calling.
        - Puede modificar el estado de la conversación (memoria).
        - Cada implementación documenta sus efectos colaterales.

    Excepciones:
        - OrchestrationError: Si la orquestación falla.
        - AgentNotFoundError: Si el agente destino no existe.
    """

    async def route(self, message: AgentMessage) -> AgentMessage:
        """Enruta un mensaje al agente apropiado y retorna la respuesta.

        El orquestador decide qué agente procesa el mensaje basándose en
        el tipo de mensaje, el dominio del contenido, o reglas de routing.

        Args:
            message: Mensaje a enrutar.

        Returns:
            Respuesta del agente destino como AgentMessage.

        Raises:
            AgentNotFoundError: Si no hay agente para el tipo de mensaje.
            OrchestrationError: Si falla el procesamiento.
        """
        ...

    async def delegate(self, from_agent: str, to_agent: str, task: dict) -> dict:
        """Delega una tarea de un agente a otro.

        Permite que un agente solicite ayuda a otro para completar una subtarea.
        El agente origen pierde control sobre la tarea hasta que el destino responda.

        Args:
            from_agent: Agente que delega la tarea.
            to_agent: Agente que recibe la tarea.
            task: Descripción de la tarea a delegar (dict flexible).

        Returns:
            Resultado de la tarea delegada como dict.

        Raises:
            AgentNotFoundError: Si alguno de los agentes no existe.
            OrchestrationError: Si falla la delegación.
        """
        ...
