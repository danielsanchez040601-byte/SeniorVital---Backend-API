"""NutritionAgent tests — chat, adapter, prompts, registration."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.orchestration.agent_protocol import AgentRequest, AgentResponse


# ── Fixtures ──


@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.generate = AsyncMock()
    llm.model = "phi3:mini"
    return llm


@pytest.fixture
def mock_user_data():
    ud = AsyncMock()
    data = MagicMock()
    data.profile = {"name": "María", "age": 72}
    data.health_profile = {"conditions": ["diabetes"]}
    data.preferences = {"dietary_restrictions": ["sin azúcar"]}
    ud.get_user_data = AsyncMock(return_value=data)
    return ud


@pytest.fixture
def mock_tools():
    rag_tool = MagicMock()
    rag_tool.name = "rag_search"
    rag_tool.description = "Search nutrition knowledge base"
    rag_tool.parameters = {"query": {"type": "string"}}

    safety_tool = MagicMock()
    safety_tool.name = "safety_check"
    safety_tool.description = "Check if recommendation is safe"
    safety_tool.parameters = {"user_id": {"type": "integer"}}

    return [rag_tool, safety_tool]


@pytest.fixture
def nutrition_agent(mock_llm, mock_user_data, mock_tools):
    from src.agents.nutrition.agent import NutritionAgent
    return NutritionAgent(llm=mock_llm, user_data=mock_user_data, tools=mock_tools)


@pytest.fixture
def nutrition_adapter(nutrition_agent):
    from src.agents.nutrition.adapter import NutritionAgentAdapter
    return NutritionAgentAdapter(nutrition_agent)


# ── NutritionAgent Tests ──


class TestNutritionAgentChat:
    """Tests for NutritionAgent.chat()."""

    @pytest.mark.asyncio
    async def test_chat_returns_response(self, nutrition_agent, mock_llm):
        mock_llm.generate = AsyncMock(
            return_value='{"thought": "El usuario pregunta sobre nutrición.", "final_answer": "Te recomiendo una dieta equilibrada con verduras y proteínas magras."}'
        )
        response = await nutrition_agent.chat(user_id=1, message="¿Qué debo comer?")
        assert "dieta" in response.lower() or "comer" in response.lower()

    @pytest.mark.asyncio
    async def test_chat_empty_response_uses_fallback(self, nutrition_agent, mock_llm):
        mock_llm.generate = AsyncMock(return_value="")
        response = await nutrition_agent.chat(user_id=1, message="test")
        assert "Disculpa" in response

    @pytest.mark.asyncio
    async def test_chat_uses_rag_search(self, nutrition_agent, mock_llm):
        mock_llm.generate = AsyncMock(
            return_value='{"thought": "Busco info sobre diabetes", "action": "rag_search", "action_input": {"query": "diabetes alimentación"}}'
        )
        await nutrition_agent.chat(user_id=1, message="¿Qué como con diabetes?")
        # ReAct engine should have tried to call rag_search
        assert mock_llm.generate.called


class TestNutritionAgentProcess:
    """Tests for NutritionAgent.process (entry point S3-03)."""

    @pytest.mark.asyncio
    async def test_process_returns_response(self, nutrition_agent, mock_llm):
        mock_llm.generate = AsyncMock(
            return_value='{"thought": "El usuario pregunta sobre hidratación.", "final_answer": "Te recomiendo beber 1.5 litros de agua al día."}'
        )
        request = AgentRequest(message="¿Cuánta agua debo tomar?", user_id=1)
        response = await nutrition_agent.process(request)
        assert "agua" in response.lower()

    @pytest.mark.asyncio
    async def test_process_delegates_to_chat(self, nutrition_agent, mock_llm):
        mock_llm.generate = AsyncMock(
            return_value='{"thought": "Respuesta de prueba.", "final_answer": "Prueba exitosa."}'
        )
        request = AgentRequest(message="test", user_id=7)
        response = await nutrition_agent.process(request)
        assert "prueba" in response.lower()


# ── NutritionAgentAdapter Tests ──


class TestNutritionAgentAdapter:
    """Tests for NutritionAgentAdapter."""

    @pytest.mark.asyncio
    async def test_adapter_handle(self, nutrition_adapter):
        request = AgentRequest(message="¿Qué debo comer hoy?", user_id=1)
        response = await nutrition_adapter.handle(request)
        assert isinstance(response, AgentResponse)
        assert response.safety_level == "safe"
        assert response.metadata["agent"] == "nutrition"

    @pytest.mark.asyncio
    async def test_adapter_error_returns_fallback(self, nutrition_adapter):
        nutrition_adapter._agent._llm.generate = AsyncMock(
            side_effect=Exception("LLM timeout")
        )
        request = AgentRequest(message="test", user_id=1)
        response = await nutrition_adapter.handle(request)
        assert "Disculpa" in response.text

    def test_adapter_can_handle_nutrition(self, nutrition_adapter):
        assert nutrition_adapter.can_handle("nutrition", 0.8) is True

    def test_adapter_cannot_handle_other_domain(self, nutrition_adapter):
        assert nutrition_adapter.can_handle("analytics", 0.8) is False

    def test_adapter_low_confidence_rejected(self, nutrition_adapter):
        assert nutrition_adapter.can_handle("nutrition", 0.3) is False

    def test_adapter_attributes(self, nutrition_adapter):
        assert nutrition_adapter.name == "nutrition"
        assert nutrition_adapter.domain == "nutrition"
        assert "nutrición" in nutrition_adapter.description.lower()


# ── NutritionPromptBuilder Tests ──


class TestNutritionPromptBuilder:
    """Tests for NutritionPromptBuilder."""

    def test_build_returns_tuple(self):
        from src.agents.nutrition.prompts import NutritionPromptBuilder
        builder = NutritionPromptBuilder()
        system, user = builder.build(
            user_message="¿Qué como?",
            user_profile={"name": "María", "age": 72},
            conversation_history=[],
        )
        assert isinstance(system, str)
        assert isinstance(user, str)

    def test_system_prompt_contains_rules(self):
        from src.agents.nutrition.prompts import NutritionPromptBuilder
        builder = NutritionPromptBuilder()
        system, _ = builder.build(
            user_message="test",
            user_profile={},
            conversation_history=[],
        )
        assert "REGLAS" in system
        assert "español" in system.lower()

    def test_system_prompt_includes_tools(self):
        from src.agents.nutrition.prompts import NutritionPromptBuilder
        builder = NutritionPromptBuilder()
        tool = MagicMock()
        tool.name = "rag_search"
        tool.description = "Search knowledge base"
        system, _ = builder.build(
            user_message="test",
            user_profile={},
            conversation_history=[],
            available_tools=[tool],
        )
        assert "rag_search" in system

    def test_user_prompt_includes_profile(self):
        from src.agents.nutrition.prompts import NutritionPromptBuilder
        builder = NutritionPromptBuilder()
        _, user = builder.build(
            user_message="test",
            user_profile={"name": "María", "age": 72},
            conversation_history=[],
        )
        assert "María" in user
        assert "72" in user


# ── Registration Tests ──


class TestNutritionRegistration:
    """Tests for NutritionAgent registration in Orchestrator."""

    def test_adapter_has_required_attributes(self, nutrition_adapter):
        assert hasattr(nutrition_adapter, "name")
        assert hasattr(nutrition_adapter, "domain")
        assert hasattr(nutrition_adapter, "handle")
        assert hasattr(nutrition_adapter, "can_handle")
        assert callable(nutrition_adapter.handle)
        assert callable(nutrition_adapter.can_handle)
