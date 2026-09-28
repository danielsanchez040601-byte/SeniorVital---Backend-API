"""Shared fixtures for multi-agent integration tests.

Provides fully wired orchestrator, agents, and mock LLM for deterministic testing.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.orchestration import AgentMessage
from src.orchestration.agent_protocol import AgentRequest, AgentResponse
from src.orchestration.router import OrchestratorAgent


# ── Mock LLM ──


@pytest.fixture
def mock_llm():
    """Configurable mock LLM for deterministic responses."""
    llm = AsyncMock()
    llm.generate = AsyncMock()
    llm.model = "phi3:mini"
    return llm


# ── Mock Agents ──


@pytest.fixture
def nutrition_agent():
    """Mock NutritionAgent adapter."""
    agent = AsyncMock()
    agent.name = "nutrition"
    agent.domain = "nutrition"
    agent.description = "Agente de nutrición"
    agent.handle = AsyncMock(
        return_value=AgentResponse(
            text="Para una buena nutrición, incluye proteínas magras y verduras en cada comida.",
            safety_level="safe",
            tool_chain=["rag_search"],
            metadata={"agent": "nutrition", "domain": "nutrition"},
        )
    )
    agent.can_handle = MagicMock(return_value=True)
    return agent


@pytest.fixture
def wellness_agent():
    """Mock WellnessCoachAgent adapter."""
    agent = AsyncMock()
    agent.name = "wellness_coach"
    agent.domain = "general"
    agent.description = "Agente general de bienestar"
    agent.handle = AsyncMock(
        return_value=AgentResponse(
            text="¡Hola! Estoy aquí para ayudarte con tu bienestar.",
            safety_level="safe",
            tool_chain=[],
            metadata={"agent": "wellness_coach", "domain": "general"},
        )
    )
    agent.can_handle = MagicMock(return_value=True)
    return agent


@pytest.fixture
def analytics_agent():
    """Mock AnalyticsAgent adapter."""
    agent = AsyncMock()
    agent.name = "analytics"
    agent.domain = "analytics"
    agent.description = "Agente de analítica"
    agent.handle = AsyncMock(
        return_value=AgentResponse(
            text="Has completado 12 sesiones esta semana con un RPE promedio de 6.5.",
            safety_level="safe",
            tool_chain=["get_progress"],
            metadata={"agent": "analytics", "domain": "analytics"},
        )
    )
    agent.can_handle = MagicMock(return_value=True)
    return agent


@pytest.fixture
def motivation_agent():
    """Mock MotivationAgent adapter."""
    agent = AsyncMock()
    agent.name = "motivation"
    agent.domain = "motivation"
    agent.description = "Agente de motivación"
    agent.handle = AsyncMock(
        return_value=AgentResponse(
            text="¡Sigue así! Cada día es una oportunidad para mejorar.",
            safety_level="safe",
            tool_chain=["rag_search"],
            metadata={"agent": "motivation", "domain": "motivation"},
        )
    )
    agent.can_handle = MagicMock(return_value=True)
    return agent


@pytest.fixture
def critical_agent():
    """Mock agent that returns critical safety level."""
    agent = AsyncMock()
    agent.name = "dangerous"
    agent.domain = "danger"
    agent.handle = AsyncMock(
        return_value=AgentResponse(
            text="¡Corre rápido sin calentar!",
            safety_level="critical",
            tool_chain=[],
        )
    )
    return agent


@pytest.fixture
def failing_agent():
    """Mock agent that always raises an exception."""
    agent = AsyncMock()
    agent.name = "failing"
    agent.domain = "fail"
    agent.handle = AsyncMock(side_effect=Exception("Agent crashed"))
    return agent


# ── Orchestrator Fixtures ──


@pytest.fixture
def orchestrator(mock_llm):
    """Fresh OrchestratorAgent with no agents registered."""
    return OrchestratorAgent(mock_llm)


@pytest.fixture
def wired_orchestrator(mock_llm, nutrition_agent, wellness_agent, analytics_agent, motivation_agent):
    """Fully wired OrchestratorAgent with all agents registered."""
    orch = OrchestratorAgent(mock_llm)
    orch.register_agent("nutrition", nutrition_agent)
    orch.register_agent("general", wellness_agent)
    orch.register_agent("analytics", analytics_agent)
    orch.register_agent("motivation", motivation_agent)
    orch.set_fallback(wellness_agent)
    return orch


# ── Message Helpers ──


def make_user_message(text: str, user_id: int = 1, correlation_id: str = "") -> AgentMessage:
    """Create a user AgentMessage."""
    kwargs = {
        "from_agent": "user",
        "to_agent": "orchestrator",
        "content": {"message": text, "user_id": user_id},
        "message_type": "query",
    }
    if correlation_id:
        kwargs["correlation_id"] = correlation_id
    return AgentMessage(**kwargs)


def make_classification_response(domain: str, confidence: float = 0.9) -> str:
    """Create a mock LLM classification response."""
    return json.dumps({"domain": domain, "confidence": confidence, "reason": "test"})
