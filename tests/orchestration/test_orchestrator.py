"""Orchestrator Agent tests — routing, delegation, safety, adapter."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.orchestration import AgentMessage, OrchestrationError
from src.orchestration.agent_protocol import (
    AgentRequest,
    AgentResponse,
    IntentResult,
)
from src.orchestration.router import IntentClassifier, OrchestratorAgent


# ── Fixtures ──


@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.generate = AsyncMock()
    llm.model = "phi3:mini"
    return llm


@pytest.fixture
def classifier(mock_llm):
    return IntentClassifier(mock_llm)


@pytest.fixture
def orchestrator(mock_llm):
    return OrchestratorAgent(mock_llm)


@pytest.fixture
def mock_agent():
    agent = AsyncMock()
    agent.name = "test_agent"
    agent.domain = "test"
    agent.description = "Test agent"
    agent.handle = AsyncMock(
        return_value=AgentResponse(
            text="Test response",
            safety_level="safe",
            tool_chain=["test_tool"],
        )
    )
    agent.can_handle = AsyncMock(return_value=True)
    return agent


@pytest.fixture
def fallback_agent():
    agent = AsyncMock()
    agent.name = "wellness_coach"
    agent.domain = "general"
    agent.description = "Fallback agent"
    agent.handle = AsyncMock(
        return_value=AgentResponse(
            text="Fallback response",
            safety_level="safe",
            tool_chain=[],
        )
    )
    agent.can_handle = AsyncMock(return_value=True)
    return agent


@pytest.fixture
def user_message():
    return AgentMessage(
        from_agent="user",
        to_agent="orchestrator",
        content={"message": "¿Qué debo comer hoy?", "user_id": 1, "user_profile": {}, "conversation_history": []},
        message_type="query",
    )


# ── IntentClassifier Tests ──


class TestIntentClassifierKeywords:
    """Tests for keyword-based intent classification."""

    def test_nutrition_keywords(self, classifier):
        result = classifier._classify_by_keywords("¿Qué debo comer hoy?")
        assert result is not None
        assert result.domain == "nutrition"
        assert result.confidence > 0

    def test_analytics_keywords(self, classifier):
        result = classifier._classify_by_keywords("¿Cómo voy con mis ejercicios?")
        assert result is not None
        assert result.domain == "analytics"
        assert result.confidence > 0

    def test_motivation_keywords(self, classifier):
        result = classifier._classify_by_keywords("Me siento triste y aburrido")
        assert result is not None
        assert result.domain == "motivation"
        assert result.confidence > 0

    def test_safety_keywords(self, classifier):
        result = classifier._classify_by_keywords("¿Es seguro correr con presión alta?")
        assert result is not None
        assert result.domain == "safety"
        assert result.confidence > 0

    def test_no_match_returns_none(self, classifier):
        result = classifier._classify_by_keywords("Hola")
        assert result is None


class TestIntentClassifierLLM:
    """Tests for LLM-based intent classification."""

    @pytest.mark.asyncio
    async def test_classify_with_llm(self, classifier, mock_llm):
        mock_llm.generate = AsyncMock(
            return_value=json.dumps({"domain": "nutrition", "confidence": 0.9})
        )
        result = await classifier.classify("¿Qué debo comer?")
        assert result.domain == "nutrition"
        assert result.confidence == 0.9

    @pytest.mark.asyncio
    async def test_classify_fallback_on_llm_error(self, classifier, mock_llm):
        mock_llm.generate = AsyncMock(side_effect=Exception("LLM error"))
        result = await classifier.classify("Hola")
        assert result.domain == "general"
        assert result.confidence == 1.0


# ── OrchestratorAgent Tests ──


class TestOrchestratorAgent:
    """Tests for OrchestratorAgent routing and delegation."""

    @pytest.mark.asyncio
    async def test_route_to_registered_agent(self, orchestrator, mock_agent, user_message):
        orchestrator.register_agent("nutrition", mock_agent)
        # Override classifier to return high confidence
        orchestrator._classifier = MagicMock()
        orchestrator._classifier.classify = AsyncMock(
            return_value=IntentResult(domain="nutrition", confidence=0.9)
        )
        response = await orchestrator.route(user_message)

        assert response.content["response"] == "Test response"
        assert response.content["agent"] == "test_agent"
        mock_agent.handle.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_when_no_agent(self, orchestrator, fallback_agent, user_message):
        orchestrator.set_fallback(fallback_agent)
        # Override classifier to return low confidence → fallback
        orchestrator._classifier = MagicMock()
        orchestrator._classifier.classify = AsyncMock(
            return_value=IntentResult(domain="unknown", confidence=0.3)
        )
        response = await orchestrator.route(user_message)

        assert response.content["response"] == "Fallback response"
        fallback_agent.handle.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_on_agent_error(self, orchestrator, fallback_agent, user_message):
        failing_agent = AsyncMock()
        failing_agent.name = "failing"
        failing_agent.handle = AsyncMock(side_effect=Exception("Agent crashed"))

        orchestrator.register_agent("nutrition", failing_agent)
        orchestrator.set_fallback(fallback_agent)
        orchestrator._classifier = MagicMock()
        orchestrator._classifier.classify = AsyncMock(
            return_value=IntentResult(domain="nutrition", confidence=0.9)
        )

        response = await orchestrator.route(user_message)
        assert response.content["response"] == "Fallback response"

    @pytest.mark.asyncio
    async def test_safety_critical_blocks_response(self, orchestrator, user_message):
        critical_agent = AsyncMock()
        critical_agent.name = "dangerous"
        critical_agent.handle = AsyncMock(
            return_value=AgentResponse(
                text="Run fast!",
                safety_level="critical",
                tool_chain=[],
            )
        )

        orchestrator.register_agent("nutrition", critical_agent)
        orchestrator._classifier = MagicMock()
        orchestrator._classifier.classify = AsyncMock(
            return_value=IntentResult(domain="nutrition", confidence=0.9)
        )
        response = await orchestrator.route(user_message)

        assert "profesional" in response.content["response"]
        assert response.content["safety_level"] == "critical"

    @pytest.mark.asyncio
    async def test_no_agent_returns_message(self, orchestrator, user_message):
        orchestrator._agents = {}
        orchestrator._fallback_agent = None
        orchestrator._classifier = MagicMock()
        orchestrator._classifier.classify = AsyncMock(
            return_value=IntentResult(domain="unknown", confidence=0.9)
        )
        response = await orchestrator.route(user_message)

        assert "no puedo ayudar" in response.content["response"].lower()

    @pytest.mark.asyncio
    async def test_register_and_select_agent(self, orchestrator, mock_agent):
        orchestrator.register_agent("test", mock_agent)
        assert "test" in orchestrator._agents
        assert orchestrator._agents["test"] is mock_agent

    @pytest.mark.asyncio
    async def test_delegate_between_agents(self, orchestrator, mock_agent):
        orchestrator.register_agent("agent_a", mock_agent)
        orchestrator.register_agent("agent_b", mock_agent)
        result = await orchestrator.delegate(
            "agent_a", "agent_b", {"message": "test", "user_id": 1}
        )
        assert "text" in result


# ── CoachAdapter Tests ──


class TestCoachAdapter:
    """Tests for WellnessCoachAgentAdapter."""

    @pytest.mark.asyncio
    async def test_adapter_handle(self):
        from src.agents.wellness.coach_adapter import WellnessCoachAgentAdapter

        mock_coach = AsyncMock()
        mock_coach.chat = AsyncMock(return_value="Hola, ¿cómo estás?")

        adapter = WellnessCoachAgentAdapter(mock_coach)
        request = AgentRequest(message="Hola", user_id=1)
        response = await adapter.handle(request)

        assert response.text == "Hola, ¿cómo estás?"
        assert response.safety_level == "safe"
        mock_coach.chat.assert_called_once_with(user_id=1, message="Hola")

    @pytest.mark.asyncio
    async def test_adapter_always_can_handle(self):
        from src.agents.wellness.coach_adapter import WellnessCoachAgentAdapter

        mock_coach = AsyncMock()
        adapter = WellnessCoachAgentAdapter(mock_coach)

        assert adapter.can_handle("anything", 0.5) is True

    @pytest.mark.asyncio
    async def test_adapter_error_returns_fallback(self):
        from src.agents.wellness.coach_adapter import WellnessCoachAgentAdapter

        mock_coach = AsyncMock()
        mock_coach.chat = AsyncMock(side_effect=Exception("LLM timeout"))

        adapter = WellnessCoachAgentAdapter(mock_coach)
        request = AgentRequest(message="test", user_id=1)
        response = await adapter.handle(request)

        assert "Disculpa" in response.text
        assert response.safety_level == "safe"

    def test_adapter_attributes(self):
        from src.agents.wellness.coach_adapter import WellnessCoachAgentAdapter

        mock_coach = AsyncMock()
        adapter = WellnessCoachAgentAdapter(mock_coach)

        assert adapter.name == "wellness_coach"
        assert adapter.domain == "general"
        assert "bienestar" in adapter.description.lower()
