"""Pruebas de integración automatizadas para el endpoint /api/v1/chat.

Valida el ciclo ReAct iterativo, consulta y persistencia en PostgresMemoryStore,
tool calling dinámico y aplicación de guardrails clínicos.
"""

import json
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.chat import get_wellness_coach_agent, get_memory_store
from src.agents.wellness.coach import WellnessCoachAgent
from src.agents.wellness.config import WellnessConfig
from src.agents.nutrition.agent import NutritionAgent
from src.memory import Message
from src.tools import Tool, ToolResult


class SpyMemoryStore:
    """Implementación de MemoryStore para verificar llamadas a persistencia."""

    def __init__(self):
        self.history_calls = []
        self.added_messages = []
        self._storage = {}

    async def get_history(self, user_id: str, limit: int = 20):
        self.history_calls.append((user_id, limit))
        return self._storage.get(str(user_id), [])[-limit:]

    async def add_message(self, user_id: str, message: Message):
        self.added_messages.append((user_id, message))
        self._storage.setdefault(str(user_id), []).append(message)

    async def clear_history(self, user_id: str):
        self._storage.pop(str(user_id), None)


class MockTool(Tool):
    """Herramienta simulada para pruebas deterministas."""

    def __init__(self, name: str, return_data: dict):
        self.name = name
        self.description = f"Mock tool: {name}"
        self.return_data = return_data
        self.calls = []

    def validate_args(self, **kwargs) -> bool:
        return True

    async def execute(self, **kwargs) -> ToolResult:
        self.calls.append(kwargs)
        return ToolResult(success=True, data=self.return_data, tool_name=self.name)


@pytest.fixture
def spy_memory():
    return SpyMemoryStore()


@pytest.fixture
def mock_user_data():
    svc = AsyncMock()
    svc.get_user_data.return_value = MagicMock(
        profile={"age": 72, "name": "Carmen", "city": "Madrid"},
        health_profile={"medical_restrictions": ["osteoartritis de rodilla"]},
        preferences={},
    )
    return svc


def test_chat_endpoint_react_cycle_with_tools_and_memory(spy_memory, mock_user_data):
    """Verifica que una consulta clínica active ReAct, invoque herramientas dinámicamente y persista en memoria."""
    mock_llm = AsyncMock()
    # Turno 1: Decide invocar safety_check; Turno 2: Responde con recomendación clínica adaptada
    mock_llm.generate.side_effect = [
        json.dumps({
            "thought": "El paciente menciona dolor de rodilla; debo evaluar restricciones de seguridad.",
            "action": "safety_check",
            "action_input": {"activity": "flexiones de rodilla", "user_id": 1}
        }),
        json.dumps({
            "thought": "Restricción confirmada. Recomiendo ejercicios en silla sin impacto.",
            "final_answer": "Para la osteoartritis de rodilla, es preferible realizar extensiones suaves sentado en silla sin peso adicional."
        })
    ]

    safety_tool = MockTool("safety_check", {"safe": False, "warnings": ["Evitar flexión > 90 grados"]})
    config = WellnessConfig(max_react_iterations=3)

    agent = WellnessCoachAgent(
        llm=mock_llm,
        user_data=mock_user_data,
        tools=[safety_tool],
        memory_store=spy_memory,
        config=config,
    )

    app.dependency_overrides[get_wellness_coach_agent] = lambda: agent
    app.dependency_overrides[get_memory_store] = lambda: spy_memory

    try:
        client = TestClient(app)
        payload = {
            "user_id": "42",
            "query": "¿Puedo hacer sentadillas si me duelen las rodillas?"
        }
        response = client.post("/api/v1/chat", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Validación de respuesta y seguridad
        assert "osteoartritis" in data["response"].lower() or "rodilla" in data["response"].lower()
        assert data["is_safe"] is True

        # Validación de telemetría estructurada
        telemetry = data["telemetry"]
        assert telemetry is not None
        assert telemetry["iterations"] == 2
        assert "safety_check" in telemetry["tool_calls"]
        assert telemetry["steps_count"] == 2
        assert telemetry["has_memory"] is True
        assert telemetry["mode"] == "react_engine"

        # Validación de persistencia en PostgresMemoryStore
        assert len(spy_memory.history_calls) >= 1
        assert spy_memory.history_calls[0][0] == "42"

        # Deben persistirse dos mensajes: el del usuario y el del asistente
        assert len(spy_memory.added_messages) == 2
        assert spy_memory.added_messages[0][0] == "42"
        assert spy_memory.added_messages[0][1].role == "user"
        assert spy_memory.added_messages[0][1].content == payload["query"]

        assert spy_memory.added_messages[1][0] == "42"
        assert spy_memory.added_messages[1][1].role == "assistant"
        assert spy_memory.added_messages[1][1].content == data["response"]

        # Comprobar que la herramienta se invocó efectivamente
        assert len(safety_tool.calls) == 1

    finally:
        app.dependency_overrides.clear()


def test_chat_endpoint_direct_response_without_tools(spy_memory, mock_user_data):
    """Verifica que una consulta general no invoque herramientas innecesariamente."""
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = json.dumps({
        "thought": "Es un saludo cordial de rutina, respondo directamente.",
        "final_answer": "¡Hola Carmen! ¿Cómo te sientes hoy para realizar tus actividades suaves?"
    })

    tool = MockTool("exercise_catalog", {"count": 10})
    config = WellnessConfig(max_react_iterations=3)

    agent = WellnessCoachAgent(
        llm=mock_llm,
        user_data=mock_user_data,
        tools=[tool],
        memory_store=spy_memory,
        config=config,
    )

    app.dependency_overrides[get_wellness_coach_agent] = lambda: agent
    app.dependency_overrides[get_memory_store] = lambda: spy_memory

    try:
        client = TestClient(app)
        payload = {"user_id": "1", "query": "¡Buenos días coach!"}
        response = client.post("/api/v1/chat", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "hola" in data["response"].lower()
        assert data["is_safe"] is True
        assert data["telemetry"]["iterations"] == 1
        assert data["telemetry"]["tool_calls"] == []
        assert len(tool.calls) == 0  # No debe llamar herramientas estáticamente

        # Memoria guardada
        assert len(spy_memory.added_messages) == 2

    finally:
        app.dependency_overrides.clear()


def test_chat_endpoint_guardrails_activation(mock_user_data):
    """Verifica que si la respuesta contiene prescripciones farmacológicas, se active el guardrail determinístico."""
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = json.dumps({
        "thought": "Respondiendo a consulta de dolor.",
        "final_answer": "Para el dolor agudo tómate 600mg de ibuprofeno cada 8 horas."
    })

    agent = WellnessCoachAgent(
        llm=mock_llm,
        user_data=mock_user_data,
        tools=[],
        memory_store=None,
        config=WellnessConfig(),
    )

    app.dependency_overrides[get_wellness_coach_agent] = lambda: agent

    try:
        client = TestClient(app)
        payload = {"user_id": "1", "query": "Me duele mucho la espalda, ¿qué tomo?"}
        response = client.post("/api/v1/chat", json=payload)

        assert response.status_code == 200
        data = response.json()
        # Debe haber sustituido la respuesta insegura
        assert "no estoy autorizado para recomendar medicamentos" in data["response"]
        assert data["is_safe"] is False

    finally:
        app.dependency_overrides.clear()


def test_chat_endpoint_delegation_to_nutrition_agent():
    """Verifica que una consulta sobre dieta y nutrición sea delegada dinámicamente al NutritionAgent."""
    mock_nutrition = AsyncMock(spec=NutritionAgent)
    mock_nutrition.chat_with_trace = AsyncMock(
        return_value=(
            "Para adultos mayores con diabetes, recomendamos priorizar fibra soluble, verduras al vapor y proteínas magras en el almuerzo.",
            MagicMock(iterations=1, steps=[MagicMock(action="clinical_dietary_check")]),
        )
    )
    mock_nutrition.chat = AsyncMock(
        return_value="Para adultos mayores con diabetes, recomendamos priorizar fibra soluble, verduras al vapor y proteínas magras en el almuerzo."
    )

    from src.api.chat import get_nutrition_agent
    app.dependency_overrides[get_nutrition_agent] = lambda: mock_nutrition

    try:
        client = TestClient(app)
        payload = {
            "user_id": "10",
            "query": "¿Qué dieta y alimentos son recomendados para mi almuerzo si tengo diabetes?",
        }
        response = client.post("/api/v1/chat", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "diabetes" in data["response"].lower()
        assert data["is_safe"] is True

        telemetry = data["telemetry"]
        assert telemetry is not None
        assert telemetry["agent_selected"] == "nutrition"
        assert telemetry["correlation_id"] is not None
        assert telemetry["mode"] == "supervisor_orchestration"

    finally:
        app.dependency_overrides.clear()

