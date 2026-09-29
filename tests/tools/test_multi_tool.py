"""Multi-tool chain tests — agent uses multiple tools in sequence."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from src.agents.wellness.coach import WellnessCoachAgent
from src.agents.wellness.config import WellnessConfig
from src.memory import Message
from src.tools import ToolResult


class FakeMemoryStore:
    def __init__(self):
        self.messages = {}

    async def get_history(self, user_id, limit=20):
        return self.messages.get(user_id, [])[-limit:]

    async def add_message(self, user_id, message):
        self.messages.setdefault(user_id, []).append(message)

    async def clear_history(self, user_id):
        self.messages.pop(user_id, None)


class FakeTool:
    def __init__(self, name, response):
        self.name = name
        self.description = f"Fake: {name}"
        self._response = response

    async def execute(self, **kwargs):
        return ToolResult(success=True, data=self._response, tool_name=self.name)

    def validate_args(self, **kwargs):
        return True


class FailingTool:
    def __init__(self, name="failing_tool"):
        self.name = name
        self.description = f"Failing: {name}"

    async def execute(self, **kwargs):
        return ToolResult(success=False, error="Simulated failure", tool_name=self.name)

    def validate_args(self, **kwargs):
        return True


@pytest.fixture
def mock_llm():
    return AsyncMock()


@pytest.fixture
def mock_user_data():
    svc = AsyncMock()
    svc.get_user_data.return_value = MagicMock(
        profile={"age": 70, "name": "Juan"},
        health_profile={"medical_restrictions": []},
        preferences={},
    )
    return svc


@pytest.fixture
def memory():
    return FakeMemoryStore()


@pytest.fixture
def config():
    return WellnessConfig(max_react_iterations=3, conversation_history_limit=5)


@pytest.mark.asyncio
async def test_chain_safety_check_then_catalog(mock_llm, mock_user_data, memory, config):
    """Agent calls safety_check first, then exercise_catalog based on result."""
    tools = [
        FakeTool("safety_check", {"safe": True, "warnings": [], "restrictions": []}),
        FakeTool("exercise_catalog", {"exercises": [{"name": "Caminata"}], "count": 1}),
    ]

    responses = [
        json.dumps({"thought": "Debo verificar seguridad", "action": "safety_check", "action_input": {"user_id": 1, "activity": "caminata"}}),
        json.dumps({"thought": "Es seguro, busco ejercicios", "action": "exercise_catalog", "action_input": {"level": 1}}),
        "Con tu nivel, te recomiendo caminar 20 minutos diarios.",
    ]
    mock_llm.generate.side_effect = responses

    agent = WellnessCoachAgent(llm=mock_llm, user_data=mock_user_data, tools=tools, memory_store=memory, config=config)
    result = await agent.chat(user_id=1, message="¿Qué ejercicios puedo hacer?")

    assert isinstance(result, str)
    assert len(result) > 0
    assert mock_llm.generate.call_count == 3


@pytest.mark.asyncio
async def test_chain_log_habit_then_get_habits(mock_llm, mock_user_data, memory, config):
    """Agent logs a habit then retrieves habit history."""
    tools = [
        FakeTool("log_habit", {"logged": True, "type": "water", "value": 8}),
        FakeTool("get_habits", {"habits": [{"date": "2026-08-23", "water_glasses": 8}], "count": 1}),
    ]

    responses = [
        json.dumps({"thought": "Registro el agua", "action": "log_habit", "action_input": {"user_id": 1, "habit_type": "water", "value": 8}}),
        json.dumps({"thought": "Muestro historial", "action": "get_habits", "action_input": {"user_id": 1, "days": 1}}),
        "Registré 8 vasos de agua. Hoy llevas 8 vasos en total.",
    ]
    mock_llm.generate.side_effect = responses

    agent = WellnessCoachAgent(llm=mock_llm, user_data=mock_user_data, tools=tools, memory_store=memory, config=config)
    result = await agent.chat(user_id=1, message="Registré 8 vasos de agua")

    assert isinstance(result, str)
    assert mock_llm.generate.call_count == 3


@pytest.mark.asyncio
async def test_tool_failure_does_not_crash_agent(mock_llm, mock_user_data, memory, config):
    """When a tool fails, agent still produces a response."""
    tools = [FailingTool("failing_tool")]

    responses = [
        json.dumps({"thought": "Voy a usar la tool", "action": "failing_tool", "action_input": {}}),
        "Disculpa, hubo un problema técnico. ¿Podrías intentar de nuevo?",
    ]
    mock_llm.generate.side_effect = responses

    agent = WellnessCoachAgent(llm=mock_llm, user_data=mock_user_data, tools=tools, memory_store=memory, config=config)
    result = await agent.chat(user_id=1, message="test")

    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_no_tool_needed(mock_llm, mock_user_data, memory, config):
    """Agent responds directly when no tool is needed."""
    tools = [FakeTool("exercise_catalog", {"exercises": []})]

    responses = [
        "¡Hola! Soy tu coach de bienestar. ¿En qué puedo ayudarte hoy?",
    ]
    mock_llm.generate.side_effect = responses

    agent = WellnessCoachAgent(llm=mock_llm, user_data=mock_user_data, tools=tools, memory_store=memory, config=config)
    result = await agent.chat(user_id=1, message="Hola")

    assert result == "¡Hola! Soy tu coach de bienestar. ¿En qué puedo ayudarte hoy?"
    assert mock_llm.generate.call_count == 1


@pytest.mark.asyncio
async def test_chain_tool_failure_recovery(mock_llm, mock_user_data, memory, config):
    """1ra tool falla → agente recupera con 2da tool → respuesta final."""
    tools = [
        FailingTool("failing_tool"),
        FakeTool("exercise_catalog", {"exercises": [{"name": "Caminata"}], "count": 1}),
    ]

    responses = [
        json.dumps({
            "thought": "Primero intento failing_tool",
            "action": "failing_tool",
            "action_input": {},
        }),
        json.dumps({
            "thought": "La tool falló, busco ejercicios en su lugar",
            "action": "exercise_catalog",
            "action_input": {"level": "beginner"},
        }),
        json.dumps({
            "thought": "Ya tengo la info, respondo",
            "final_answer": "Encontré ejercicios para ti.",
        }),
    ]
    mock_llm.generate.side_effect = responses

    agent = WellnessCoachAgent(llm=mock_llm, user_data=mock_user_data, tools=tools, memory_store=memory, config=config)
    result = await agent.chat(user_id=1, message="Dame ejercicios")

    assert "Encontré ejercicios" in result
    assert mock_llm.generate.call_count == 3
