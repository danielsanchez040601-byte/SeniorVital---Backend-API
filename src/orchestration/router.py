"""Orchestrator Agent — router central + coordinador de flujo multiagente.

Implementa el patrón Supervisor: recibe solicitudes, clasifica intención,
delega a agentes especializados, y valida la seguridad de las respuestas.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from src.orchestration import AgentMessage, OrchestrationError
from src.orchestration.agent_protocol import (
    AgentRequest,
    AgentResponse,
    IntentResult,
)
from src.orchestration.dispatch import (
    DispatchRequest,
    DispatchResponse,
    request_to_agent_message,
    response_to_dispatch_response,
)
from src.orchestration.logging import OrchestrationLogger, create_timer
from src.services.llm import LLMService

logger = logging.getLogger(__name__)
_orchestration_log = OrchestrationLogger()

# Domain keywords mapping for intent classification
DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "nutrition": [
        "comer", "comida", "dieta", "alimento", "alimentos", "agua",
        "bebida", "nutrición", "nutricional", "calorías", "vitamina",
        "desayuno", "almuerzo", "cena", "merienda", "fruta", "verdura",
        "proteína", "carbohidrato", "grasa", "fibra",
    ],
    "analytics": [
        "ejercicio", "ejercicios", "rutina", "entrenamiento", "progreso",
        "estadística", "estadísticas", "avance", "sesiones", "actividad",
        "semanal", "diario", "meta", "objetivo", "mejorar", "rendimiento",
        "fuerza", "resistencia", "flexibilidad", "cardio",
    ],
    "motivation": [
        "triste", "aburrido", "aburrida", "motivación", "motivado",
        "ánimo", "ánimos", "emocional", "cognitivo", "memoria",
        "concentración", "juego", "juegos", "actividad mental",
        "estimulación", "bienestar emocional", "soledad", "aislamiento",
    ],
    "safety": [
        "peligro", "riesgo", "seguro", "segura", "caída", "caídas",
        "dolor", "molestia", "lesión", "lesiones", "contraindicación",
        "presión alta", "hipertensión", "diabetes", "cardíaco",
    ],
}

# Minimum confidence threshold for domain-specific routing
CONFIDENCE_THRESHOLD = 0.7


class IntentClassifier:
    """Clasifica la intención del usuario usando el LLM.

    Usa un prompt estructurado para que phi3:mini clasifique
    la intención en uno de los dominios predefinidos.
    """

    CLASSIFY_PROMPT = """Clasifica este mensaje de un adulto mayor en uno de estos dominios:
- nutrition: nutrición, dieta, comida, agua
- analytics: ejercicio, rutina, progreso, estadísticas
- motivation: bienestar emocional, cognitivo, motivación
- safety: seguridad, riesgos, salud, dolor
- general: cualquier otra cosa

Mensaje: "{message}"

Responde SOLO con este JSON:
{{"domain": "nombre_dominio", "confidence": 0.0-1.0, "reason": "razón breve"}}"""

    def __init__(self, llm: LLMService) -> None:
        self._llm = llm

    async def classify(self, message: str) -> IntentResult:
        """Clasifica el dominio de un mensaje.

        Args:
            message: Mensaje del usuario.

        Returns:
            IntentResult con dominio, confianza y keywords.
        """
        # Fast path: keyword matching
        keyword_result = self._classify_by_keywords(message)
        if keyword_result and keyword_result.confidence >= CONFIDENCE_THRESHOLD:
            logger.info(
                f"Intent classified by keywords: {keyword_result.domain} "
                f"({keyword_result.confidence:.2f})"
            )
            return keyword_result

        # Slow path: LLM classification
        try:
            prompt = self.CLASSIFY_PROMPT.format(message=message)
            response = await self._llm.generate(
                prompt,
                system="Eres un clasificador de intenciones. Responde solo en JSON.",
                format_json=True,
            )

            parsed = self._parse_classify_response(response)
            if parsed:
                result = IntentResult(
                    domain=parsed.get("domain", "general"),
                    confidence=parsed.get("confidence", 0.5),
                    keywords=[],
                    raw_llm_response=response,
                )
                logger.info(
                    f"Intent classified by LLM: {result.domain} "
                    f"({result.confidence:.2f})"
                )
                return result

        except Exception as e:
            logger.warning(f"LLM classification failed: {e}")

        # Fallback: general domain
        return IntentResult(domain="general", confidence=1.0)

    def _classify_by_keywords(self, message: str) -> IntentResult | None:
        """Clasificación rápida por keywords (sin LLM)."""
        message_lower = message.lower()
        scores: dict[str, int] = {}

        for domain, keywords in DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in message_lower)
            if score > 0:
                scores[domain] = score

        if not scores:
            return None

        best_domain = max(scores, key=scores.get)
        total_keywords = len(DOMAIN_KEYWORDS[best_domain])
        confidence = min(scores[best_domain] / 3, 1.0)  # 3 keywords = max confidence

        return IntentResult(
            domain=best_domain,
            confidence=round(confidence, 2),
            keywords=[kw for kw in DOMAIN_KEYWORDS[best_domain] if kw in message_lower],
        )

    def _parse_classify_response(self, response: str) -> dict | None:
        """Parsea la respuesta de clasificación del LLM."""
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                cleaned = "\n".join(lines).strip()
            return json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            logger.warning(f"Failed to parse classify response: {response[:200]}")
            return None


class OrchestratorAgent:
    """Orchestrator Agent — router central del sistema multiagente.

    Implementa el patrón Supervisor:
    1. Recibe solicitudes del usuario
    2. Clasifica intención (IntentClassifier)
    3. Selecciona agente destino
    4. Delega con contexto
    5. Valida seguridad de la respuesta
    6. Retorna respuesta al usuario

    Precondiciones:
        - LLM disponible para clasificación de intención.
        - Al menos un agente registrado.

    Postcondiciones:
        - route() retorna AgentMessage con respuesta.
        - Las respuestas son validadas por seguridad.

    Efectos secundarios:
        - Ejecuta clasificación vía LLM.
        - Delega a agentes que pueden ejecutar tools.
    """

    def __init__(self, llm: LLMService) -> None:
        self._llm = llm
        self._agents: dict[str, Any] = {}
        self._classifier = IntentClassifier(llm)
        self._fallback_agent: Any = None
        self._active_correlations: set[str] = set()

    def register_agent(self, name: str, agent: Any) -> None:
        """Registra un agente especializado.

        Args:
            name: Nombre único del agente.
            agent: Instancia que implementa el Agent Protocol.
        """
        self._agents[name] = agent
        logger.info(f"Registered agent: {name}")

    def set_fallback(self, agent: Any) -> None:
        """Establece el agente de fallback (WellnessCoachAgent)."""
        self._fallback_agent = agent

    async def route(self, message: AgentMessage) -> AgentMessage:
        """Enruta un mensaje al agente apropiado y retorna la respuesta.

        Args:
            message: Mensaje con content["message"] y content["user_id"].

        Returns:
            AgentMessage con la respuesta del agente.

        Raises:
            OrchestrationError: Si falla la orquestación.
        """
        correlation_id = message.correlation_id
        user_message = message.content.get("message", "")
        user_id = message.content.get("user_id", 0)
        user_profile = message.content.get("user_profile", {})
        history = message.content.get("conversation_history", [])

        _orchestration_log.route_start(correlation_id, user_id, user_message)

        # 1. Classify intent
        intent = await self._classifier.classify(user_message)
        method = "keywords" if intent.keywords else "llm"
        _orchestration_log.intent_classified(
            correlation_id, intent.domain, intent.confidence, method
        )

        # 2. Select agent
        agent = self.select_agent(intent)
        if not agent:
            _orchestration_log.fallback_activated(
                correlation_id, f"no_agent_for_{intent.domain}", "none"
            )
            return AgentMessage(
                from_agent="orchestrator",
                to_agent=message.from_agent,
                content={
                    "response": "Lo siento, no puedo ayudar con eso en este momento.",
                    "safety_level": "safe",
                },
                message_type="response",
                correlation_id=correlation_id,
            )

        agent_name = getattr(agent, "name", "unknown")
        _orchestration_log.agent_selected(correlation_id, agent_name)

        # 3. Delegate to agent
        timer = create_timer()
        try:
            request = AgentRequest(
                message=user_message,
                user_id=user_id,
                user_profile=user_profile,
                conversation_history=history,
                context={
                    "intent": intent.domain,
                    "confidence": intent.confidence,
                    "correlation_id": correlation_id,
                },
            )
            response = await agent.handle(request)
        except Exception as e:
            duration = timer[0]()
            logger.error(f"Agent {agent_name} failed: {e}")
            _orchestration_log.route_end(correlation_id, agent_name, duration)
            # Fallback
            if self._fallback_agent and self._fallback_agent is not agent:
                _orchestration_log.fallback_activated(
                    correlation_id, f"agent_error: {e}", getattr(self._fallback_agent, "name", "fallback")
                )
                request = AgentRequest(
                    message=user_message,
                    user_id=user_id,
                    user_profile=user_profile,
                    conversation_history=history,
                )
                response = await self._fallback_agent.handle(request)
            else:
                raise OrchestrationError(
                    f"Agent {agent_name} failed and no fallback available: {e}",
                    source_agent=agent_name,
                )

        # 4. Validate safety
        if response.safety_level == "critical":
            _orchestration_log.safety_check(correlation_id, agent_name, "critical", True)
            duration = timer[0]()
            _orchestration_log.route_end(correlation_id, agent_name, duration)
            return AgentMessage(
                from_agent="orchestrator",
                to_agent=message.from_agent,
                content={
                    "response": (
                        "No puedo darte esa recomendación. "
                        "Por favor, consulta con un profesional de la salud."
                    ),
                    "safety_level": "critical",
                    "original_response": response.text,
                },
                message_type="response",
                correlation_id=correlation_id,
            )

        # 5. Return response
        duration = timer[0]()
        _orchestration_log.route_end(correlation_id, agent_name, duration)
        return AgentMessage(
            from_agent="orchestrator",
            to_agent=message.from_agent,
            content={
                "response": response.text,
                "safety_level": response.safety_level,
                "tool_chain": response.tool_chain,
                "agent": agent_name,
            },
            message_type="response",
            correlation_id=correlation_id,
        )

    async def delegate(
        self, from_agent: str, to_agent: str, task: dict, correlation_id: str = ""
    ) -> dict:
        """Delega una tarea de un agente a otro con safety validation y trazabilidad.

        Args:
            from_agent: Agente que delega.
            to_agent: Agente que recibe la tarea.
            task: Descripción de la tarea.
            correlation_id: ID de correlación para trazabilidad (opcional).

        Returns:
            Resultado de la tarea delegada.

        Raises:
            AgentNotFoundError: Si alguno de los agentes no existe.
        """
        agent = self._agents.get(to_agent)
        if not agent:
            from src.orchestration import AgentNotFoundError
            raise AgentNotFoundError(to_agent)

        _orchestration_log.delegation_start(
            correlation_id, from_agent, to_agent
        )
        timer = create_timer()

        try:
            request = AgentRequest(
                message=task.get("message", ""),
                user_id=task.get("user_id", 0),
                user_profile=task.get("user_profile", {}),
                conversation_history=task.get("conversation_history", []),
                context={
                    "delegated_by": from_agent,
                    "correlation_id": correlation_id,
                },
            )
            response = await agent.handle(request)
            success = True
        except Exception as e:
            duration = timer[0]()
            _orchestration_log.delegation_end(
                correlation_id, from_agent, to_agent, duration, False
            )
            raise

        duration = timer[0]()
        safety_level = response.safety_level

        # Safety validation (same as route())
        if safety_level == "critical":
            _orchestration_log.safety_check(
                correlation_id, to_agent, "critical", True
            )
            _orchestration_log.delegation_end(
                correlation_id, from_agent, to_agent, duration, True, safety_level
            )
            return {
                "text": (
                    "No puedo darte esa recomendación. "
                    "Por favor, consulta con un profesional de la salud."
                ),
                "safety_level": "critical",
                "blocked": True,
                "original_text": response.text,
            }

        _orchestration_log.delegation_end(
            correlation_id, from_agent, to_agent, duration, True, safety_level
        )
        return {
            "text": response.text,
            "safety_level": safety_level,
            "tool_chain": response.tool_chain,
            "metadata": response.metadata,
        }

    async def dispatch(self, request: DispatchRequest) -> DispatchResponse:
        """Despacha una solicitud estructurada (entry point S3-04).

        Flujo:
            1. Prefiere el intent provisto en la solicitud; si está vacío,
               lo clasifica con IntentClassifier.
            2. Selecciona el agente destino (select_agent).
            3. Delega con contexto y recoge la respuesta.
            4. Registra trazabilidad (dispatch_start/dispatch_end) y
               bloquea respuestas critical.

        Anti-ciclos: si el correlation_id de la solicitud coincide con el
        de un despacho ya activo en la cadena (parent_id), se lanza
        OrchestrationError — evita delegaciones recursivas.

        Args:
            request: Solicitud estructurada (DispatchRequest).

        Returns:
            DispatchResponse estructurada con agente, safety y timing.

        Raises:
            OrchestrationError: Si falla la orquestación o hay ciclo.
        """
        correlation_id = request.correlation_id or request.request_id
        user_message = request.message
        user_id = request.user_id

        _orchestration_log.dispatch_start(
            correlation_id, request.request_id, user_id, user_message, request.intent
        )
        timer = create_timer()

        # Guard anti-ciclo: rechazar reentradas con el mismo correlation_id
        if correlation_id in self._active_correlations:
            raise OrchestrationError(
                f"Delegation cycle detected for correlation_id={correlation_id}",
                source_agent="orchestrator",
            )
        self._active_correlations.add(correlation_id)

        try:
            # 1. Intent (provisto o clasificado)
            if request.intent:
                intent = IntentResult(
                    domain=request.intent, confidence=1.0, keywords=["provided"]
                )
                _orchestration_log.intent_classified(
                    correlation_id, intent.domain, intent.confidence, "provided"
                )
            else:
                intent = await self._classifier.classify(user_message)

            # 2. Seleccionar agente
            agent = self.select_agent(intent)
            if not agent:
                _orchestration_log.fallback_activated(
                    correlation_id, f"no_agent_for_{intent.domain}", "none"
                )
                return response_to_dispatch_response(
                    AgentResponse(
                        text="Lo siento, no puedo ayudar con eso en este momento.",
                        safety_level="safe",
                    ),
                    request_id=request.request_id,
                    agent="none",
                    intent=intent.domain,
                    duration_ms=timer[0](),
                )

            agent_name = getattr(agent, "name", "unknown")
            _orchestration_log.agent_selected(correlation_id, agent_name)

            # 3. Delegar con contexto
            try:
                agent_request = AgentRequest(
                    message=user_message,
                    user_id=user_id,
                    user_profile=request.context.get("user_profile", {}),
                    conversation_history=request.conversation_history,
                    context={
                        "intent": intent.domain,
                        "confidence": intent.confidence,
                        "correlation_id": correlation_id,
                        "request_id": request.request_id,
                        "payload": request.payload,
                        "parent_id": request.correlation_id,
                    },
                )
                response = await agent.handle(agent_request)
            except Exception as e:
                logger.error(f"Agent {agent_name} failed in dispatch: {e}")
                if self._fallback_agent and self._fallback_agent is not agent:
                    _orchestration_log.fallback_activated(
                        correlation_id, f"agent_error: {e}",
                        getattr(self._fallback_agent, "name", "fallback"),
                    )
                    fallback_request = AgentRequest(
                        message=user_message,
                        user_id=user_id,
                        user_profile=request.context.get("user_profile", {}),
                        conversation_history=request.conversation_history,
                    )
                    response = await self._fallback_agent.handle(fallback_request)
                    agent_name = getattr(self._fallback_agent, "name", "fallback")
                else:
                    raise OrchestrationError(
                        f"Agent {agent_name} failed and no fallback available: {e}",
                        source_agent=agent_name,
                    )

            # 4. Safety + respuesta
            blocked = response.safety_level == "critical"
            if blocked:
                response = AgentResponse(
                    text=(
                        "No puedo darte esa recomendación. "
                        "Por favor, consulta con un profesional de la salud."
                    ),
                    safety_level="critical",
                )
                _orchestration_log.safety_check(
                    correlation_id, agent_name, "critical", True
                )

            duration = timer[0]()
            _orchestration_log.dispatch_end(
                correlation_id, request.request_id, agent_name, duration,
                response.safety_level, blocked,
            )

            return response_to_dispatch_response(
                response,
                request_id=request.request_id,
                agent=agent_name,
                intent=intent.domain,
                duration_ms=duration,
                blocked=blocked,
                metadata={"correlation_id": correlation_id},
            )
        finally:
            self._active_correlations.discard(correlation_id)
    def select_agent(self, intent: IntentResult) -> Any:
        """Selecciona el agente basado en la intención clasificada.

        Reglas centralizadas (no dispersas en componentes):
        - Confianza baja (< CONFIDENCE_THRESHOLD) → agente fallback.
        - Dominio con agente registrado → ese agente.
        - Dominio sin agente → agente fallback.

        Args:
            intent: Resultado de la clasificación de intención.

        Returns:
            Agente destino o el fallback (nunca None si hay fallback).
        """
        # Low confidence → fallback
        if intent.confidence < CONFIDENCE_THRESHOLD:
            return self._fallback_agent

        # Direct mapping
        agent = self._agents.get(intent.domain)
        if agent:
            return agent

        # Fallback
        return self._fallback_agent

    # Backward-compatible alias
    _select_agent = select_agent

    async def delegate_task(
        self, agent_name: str, task: dict, correlation_id: str = ""
    ) -> dict:
        """Delega una tarea a un agente registrado (API pública).

        Wrapper de delegate() con la firma del diseño S3-01: el agente
        destino se identifica por nombre y el task es un dict flexible
        (message, user_id, user_profile, conversation_history, ...).

        Args:
            agent_name: Nombre del agente registrado (ej. "nutrition").
            task: Descripción de la tarea a delegar.
            correlation_id: ID de correlación para trazabilidad.

        Returns:
            Resultado de la tarea delegada (dict con text, safety_level,
            tool_chain, metadata; o blocked si safety critical).

        Raises:
            AgentNotFoundError: Si el agente destino no existe.
        """
        return await self.delegate(
            from_agent="orchestrator",
            to_agent=agent_name,
            task=task,
            correlation_id=correlation_id,
        )
