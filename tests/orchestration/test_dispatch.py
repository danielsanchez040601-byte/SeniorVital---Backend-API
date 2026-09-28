"""Dispatch protocol tests — DispatchRequest/Response, converters, dispatch()."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock

from src.orchestration import AgentMessage, OrchestrationError
from src.orchestration.agent_protocol import AgentResponse, IntentResult
from src.orchestration.dispatch import (
    DispatchRequest,
    DispatchResponse,
    request_to_agent_message,
    response_from_agent_message,
    response_to_dispatch_response,
)
from src.orchestration.router import OrchestratorAgent


@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.generate = AsyncMock()
    llm.model = "phi3:mini"
    return llm


@pytest.fixture
def orchestrator(mock_llm):
    return OrchestratorAgent(mock_llm)


@pytest.fixture
def nutrition_agent():
    agent = AsyncMock()
    agent.name = "nutrition"
    agent.domain = "nutrition"
    agent.description = "Agente de nutrición"
    agent.handle = AsyncMock(
        return_value=AgentResponse(
            text="Incluye proteínas magras y verduras en cada comida.",
            safety_level="safe",
            tool_chain=["rag_search"],
        )
    )
    agent.can_handle = AsyncMock(return_value=True)
    return agent


def make_request(**overrides) -> DispatchRequest:
    base = {
        "user_id": 1,
        "message": "¿Qué debo comer hoy?",
        "intent": "nutrition",
        "payload": {"macrodomain": "E"},
        "context": {"user_profile": {"age": 72}},
    }
    base.update(overrides)
    return DispatchRequest(**base)


class TestDispatchProtocol:
    """Tests de los dataclasses y conversores del protocolo dispatch."""

    def test_request_auto_generates_request_id(self):
        r1 = DispatchRequest(message="hola")
        r2 = DispatchRequest(message="hola")
        assert r1.request_id
        assert r1.request_id != r2.request_id

    def test_request_to_agent_message_roundtrip(self):
        request = make_request()
        msg = request_to_agent_message(request)
        assert msg.to_agent == "orchestrator"
        assert msg.message_type == "query"
        assert msg.content["message"] == request.message
        assert msg.content["user_id"] == request.user_id

    def test_response_from_agent_message(self):
        msg = AgentMessage(
            from_agent="orchestrator",
            to_agent="user",
            content={
                "response": "Respuesta",
                "agent": "nutrition",
                "safety_level": "safe",
                "tool_chain": ["rag_search"],
                "request_id": "abc123",
            },
            message_type="response",
        )
        resp = response_from_agent_message(msg)
        assert isinstance(resp, DispatchResponse)
        assert resp.text == "Respuesta"
        assert resp.agent == "nutrition"

    def test_response_to_dispatch_response(self):
        resp = response_to_dispatch_response(
            AgentResponse(text="X", tool_chain=["t1"]),
            request_id="req1",
            agent="nutrition",
            intent="nutrition",
            duration_ms=12.34,
        )
        assert resp.request_id == "req1"
        assert resp.agent == "nutrition"
        assert resp.duration_ms == 12.3


class TestDispatchRouting:
    """Tests de OrchestratorAgent.dispatch()."""

    @pytest.mark.asyncio
    async def test_dispatch_with_provided_intent(self, orchestrator, nutrition_agent):
        orchestrator.register_agent("nutrition", nutrition_agent)
        orchestrator.set_fallback(nutrition_agent)
        resp = await orchestrator.dispatch(make_request())
        assert resp.agent == "nutrition"
        assert resp.intent == "nutrition"
        assert resp.safety_level == "safe"
        assert resp.blocked is False
        assert resp.tool_chain == ["rag_search"]
        nutrition_agent.handle.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_classifies_intent_when_missing(self, orchestrator, nutrition_agent):
        """Sin intent provisto, el IntentClassifier debe resolver el dominio."""
        orchestrator.register_agent("nutrition", nutrition_agent)
        orchestrator.set_fallback(nutrition_agent)
        # Mock LLM que devuelve la clasificación JSON del dominio nutrition
        orchestrator._classifier.classify = AsyncMock(
            return_value=IntentResult(
                domain="nutrition", confidence=0.95,
                keywords=["comer"], raw_llm_response="",
            )
        )
        resp = await orchestrator.dispatch(
            make_request(intent="", message="¿Qué debo comer?")
        )
        assert resp.agent == "nutrition"
        assert resp.intent == "nutrition"

    @pytest.mark.asyncio
    async def test_dispatch_blocks_critical(self, orchestrator, nutrition_agent):
        nutrition_agent.handle.return_value = AgentResponse(
            text="Toma este tratamiento de presión alta",
            safety_level="critical",
        )
        orchestrator.register_agent("nutrition", nutrition_agent)
        orchestrator.set_fallback(nutrition_agent)
        resp = await orchestrator.dispatch(make_request())
        assert resp.blocked is True
        assert resp.safety_level == "critical"
        assert "profesional" in resp.text.lower()

    @pytest.mark.asyncio
    async def test_dispatch_cycle_detected(self, orchestrator, nutrition_agent):
        orchestrator.register_agent("nutrition", nutrition_agent)
        orchestrator.set_fallback(nutrition_agent)
        request = DispatchRequest(
            user_id=1, message="¿Qué debo comer?", intent="nutrition",
            correlation_id="corr-1",
        )
        await orchestrator.dispatch(request)

        # Reentrada anidada: otro agente que detona el mismo correlation_id
        # mientras siguen en curso (simulado agregando la correlación activa).
        orchestrator._active_correlations.add("corr-1")
        with pytest.raises(OrchestrationError):
            await orchestrator.dispatch(request)
        orchestrator._active_correlations.discard("corr-1")

    @pytest.mark.asyncio
    async def test_dispatch_fallback_on_agent_error(self, orchestrator, nutrition_agent):
        error_agent = AsyncMock()
        error_agent.name = "error_agent"
        error_agent.handle = AsyncMock(side_effect=RuntimeError("boom"))
        orchestrator.register_agent("nutrition", error_agent)
        orchestrator.set_fallback(nutrition_agent)
        resp = await orchestrator.dispatch(make_request())
        assert resp.agent == "nutrition"  # fallback respondió
        assert resp.safety_level == "safe"
