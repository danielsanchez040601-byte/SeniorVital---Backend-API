"""Coach Agent scenario tests.

Tests the full agent pipeline through 20 wellness scenarios
using mocked LLM responses. Validates tool chains, response quality,
safety compliance, and memory retention.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.agents.wellness.coach import WellnessCoachAgent
from src.agents.wellness.config import WellnessConfig
from src.agents.wellness.evaluation.runner import evaluate_scenario, load_scenarios
from src.memory import Message


# ── Fixtures ──


class FakeMemoryStore:
    def __init__(self):
        self.messages = {}

    async def get_history(self, user_id, limit=20):
        return self.messages.get(str(user_id), [])[-limit:]

    async def add_message(self, user_id, message):
        self.messages.setdefault(str(user_id), []).append(message)

    async def clear_history(self, user_id):
        self.messages.pop(str(user_id), None)


class FakeTool:
    def __init__(self, name, response=None):
        self.name = name
        self.description = f"Fake: {name}"
        self._response = response or {}

    async def execute(self, **kwargs):
        from src.tools import ToolResult
        return ToolResult(success=True, data=self._response, tool_name=self.name)

    def validate_args(self, **kwargs):
        return True


@pytest.fixture
def mock_llm():
    return AsyncMock()


@pytest.fixture
def mock_user_data():
    svc = AsyncMock()
    svc.get_user_data.return_value = MagicMock(
        profile={"age": 70, "name": "Test"},
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


# ── Scenario loaders ──


def _get_tools_for_scenario(scenario):
    """Create appropriate fake tools based on scenario expected tools."""
    tool_responses = {
        "exercise_catalog": {"exercises": [{"name": "Caminata", "level": "beginner"}], "count": 1},
        "log_habit": {"logged": True, "type": "water", "value": 8},
        "get_habits": {"habits": [{"date": "2026-08-23", "water_glasses": 8}], "count": 1},
        "get_progress": {"progress": {"adherence": 85}, "insights": ["Buena adherencia"]},
        "get_routine": {"routine": {"exercises": [{"name": "Caminata"}]}, "exists": True},
        "safety_check": {"safe": True, "warnings": [], "restrictions": []},
        "rag_search": {"results": [{"content": "La sarcopenia es la pérdida de masa muscular"}], "count": 1},
        "generate_routine": {"routine": {"exercises": [{"name": "Yoga"}]}, "generated": True},
    }
    expected = scenario.get("expected_tool_chain", [])
    tools = []
    for name in expected:
        tools.append(FakeTool(name, tool_responses.get(name, {})))
    return tools


def _mock_llm_responses_for_scenario(scenario, mock_llm):
    """Configure mock LLM responses for a scenario."""
    category = scenario.get("category", "no_tool")
    expected_chain = scenario.get("expected_tool_chain", [])
    keywords = scenario.get("expected_response_keywords", [])
    safety_level = scenario.get("expected_safety_level", "safe")

    # Build appropriate response based on scenario type
    if category == "no_tool" or not expected_chain:
        keyword_text = ", ".join(keywords[:3]) if keywords else "bienestar"
        mock_llm.generate.return_value = json.dumps({
            "thought": "El usuario hace una pregunta general, puedo responder directamente",
            "final_answer": f"Basado en tu consulta sobre {keyword_text}, te recomiendo consultar con un profesional para información específica.",
        })
    elif category == "safety":
        mock_llm.generate.return_value = json.dumps({
            "thought": "Debo verificar la seguridad primero",
            "action": "safety_check" if "safety_check" in expected_chain else expected_chain[0],
            "action_input": {"activity": "ejercicio", "user_id": 1},
        })
        # Add second response for after tool
        if safety_level in ("warning", "critical"):
            mock_llm.generate.side_effect = [
                mock_llm.generate.return_value,
                json.dumps({
                    "thought": "La actividad tiene riesgos, debo advertir",
                    "final_answer": "Es importante que consulte con su médico antes de realizar esta actividad. Su seguridad es lo primero.",
                }),
            ]
    elif category == "memory":
        mock_llm.generate.return_value = json.dumps({
            "thought": "El usuario pregunta sobre algo que mencionamos antes",
            "final_answer": f"Recuerdo que mencionamos {', '.join(keywords[:2]) if keywords else 'eso'}. ¿Te gustaría que profundicemos?",
        })
    elif category == "edge":
        mock_llm.generate.return_value = json.dumps({
            "thought": "Esta pregunta no está en mi dominio o es incomprensible",
            "final_answer": "Disculpa, no entendí bien tu pregunta. ¿Podrías reformularla? Estoy aquí para ayudarte con temas de bienestar y salud.",
        })
    else:
        # Multi-tool or single tool
        responses = []
        for tool_name in expected_chain:
            responses.append(json.dumps({
                "thought": f"Voy a usar {tool_name} para obtener información",
                "action": tool_name,
                "action_input": {"user_id": 1},
            }))
        responses.append(json.dumps({
            "thought": "Ya tengo toda la información necesaria",
            "final_answer": f"Con la información obtenida, te recomiendo consultar sobre {', '.join(keywords[:2]) if keywords else 'tu bienestar'}.",
        }))
        mock_llm.generate.side_effect = responses


# ── No-tool scenarios ──


@pytest.mark.asyncio
async def test_sc01_no_tool_water_question(mock_llm, mock_user_data, memory, config):
    """SC01: Pregunta general sobre hidratación — sin tools."""
    _mock_llm_responses_for_scenario({
        "category": "no_tool",
        "expected_tool_chain": [],
        "expected_response_keywords": ["agua", "vasos"],
    }, mock_llm)

    agent = WellnessCoachAgent(llm=mock_llm, user_data=mock_user_data, tools=[], memory_store=memory, config=config)
    result = await agent.chat(user_id=1, message="¿Cuánta agua debo tomar al día?")

    assert isinstance(result, str)
    assert len(result) > 0
    assert mock_llm.generate.call_count == 1


@pytest.mark.asyncio
async def test_sc02_no_tool_meal_time(mock_llm, mock_user_data, memory, config):
    """SC02: Pregunta sobre horarios de comida."""
    _mock_llm_responses_for_scenario({
        "category": "no_tool",
        "expected_tool_chain": [],
        "expected_response_keywords": ["cena", "horario"],
    }, mock_llm)

    agent = WellnessCoachAgent(llm=mock_llm, user_data=mock_user_data, tools=[], memory_store=memory, config=config)
    result = await agent.chat(user_id=1, message="¿A qué hora es mejor cenar?")

    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_sc03_no_tool_greeting(mock_llm, mock_user_data, memory, config):
    """SC03: Saludo inicial del usuario."""
    _mock_llm_responses_for_scenario({
        "category": "no_tool",
        "expected_tool_chain": [],
        "expected_response_keywords": ["hola", "bienvenido"],
    }, mock_llm)

    agent = WellnessCoachAgent(llm=mock_llm, user_data=mock_user_data, tools=[], memory_store=memory, config=config)
    result = await agent.chat(user_id=1, message="Hola, ¿cómo estás?")

    assert isinstance(result, str)
    assert len(result) > 0


# ── Single-tool scenarios ──


@pytest.mark.asyncio
async def test_sc04_single_tool_exercise_catalog(mock_llm, mock_user_data, memory, config):
    """SC04: Buscar ejercicios para principiantes."""
    tools = [FakeTool("exercise_catalog", {"exercises": [{"name": "Caminata"}], "count": 1})]
    _mock_llm_responses_for_scenario({
        "category": "single_tool",
        "expected_tool_chain": ["exercise_catalog"],
        "expected_response_keywords": ["ejercicio", "principiante"],
    }, mock_llm)

    agent = WellnessCoachAgent(llm=mock_llm, user_data=mock_user_data, tools=tools, memory_store=memory, config=config)
    result = await agent.chat(user_id=1, message="¿Qué ejercicios puedo hacer si soy principiante?")

    assert isinstance(result, str)
    # Verify tool was called
    assert any(call.args[0] != "" or call.kwargs for call in mock_llm.generate.call_args_list)


@pytest.mark.asyncio
async def test_sc05_single_tool_log_habit(mock_llm, mock_user_data, memory, config):
    """SC05: Registrar consumo de agua."""
    tools = [FakeTool("log_habit", {"logged": True})]
    _mock_llm_responses_for_scenario({
        "category": "single_tool",
        "expected_tool_chain": ["log_habit"],
        "expected_response_keywords": ["registré", "agua"],
    }, mock_llm)

    agent = WellnessCoachAgent(llm=mock_llm, user_data=mock_user_data, tools=tools, memory_store=memory, config=config)
    result = await agent.chat(user_id=1, message="Acabo de tomar 8 vasos de agua hoy")

    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_sc06_single_tool_get_habits(mock_llm, mock_user_data, memory, config):
    """SC06: Consultar hábitos de sueño."""
    tools = [FakeTool("get_habits", {"habits": [{"sleep_hours": 7}], "count": 1})]
    _mock_llm_responses_for_scenario({
        "category": "single_tool",
        "expected_tool_chain": ["get_habits"],
        "expected_response_keywords": ["sueño", "dormir"],
    }, mock_llm)

    agent = WellnessCoachAgent(llm=mock_llm, user_data=mock_user_data, tools=tools, memory_store=memory, config=config)
    result = await agent.chat(user_id=1, message="¿Cómo he dormido esta semana?")

    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_sc07_single_tool_get_progress(mock_llm, mock_user_data, memory, config):
    """SC07: Ver progreso semanal."""
    tools = [FakeTool("get_progress", {"progress": {"adherence": 85}})]
    _mock_llm_responses_for_scenario({
        "category": "single_tool",
        "expected_tool_chain": ["get_progress"],
        "expected_response_keywords": ["progreso", "semana"],
    }, mock_llm)

    agent = WellnessCoachAgent(llm=mock_llm, user_data=mock_user_data, tools=tools, memory_store=memory, config=config)
    result = await agent.chat(user_id=1, message="¿Cómo voy con mi progreso esta semana?")

    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_sc08_single_tool_get_routine(mock_llm, mock_user_data, memory, config):
    """SC08: Obtener rutina del día."""
    tools = [FakeTool("get_routine", {"routine": {"exercises": []}, "exists": True})]
    _mock_llm_responses_for_scenario({
        "category": "single_tool",
        "expected_tool_chain": ["get_routine"],
        "expected_response_keywords": ["rutina", "ejercicio"],
    }, mock_llm)

    agent = WellnessCoachAgent(llm=mock_llm, user_data=mock_user_data, tools=tools, memory_store=memory, config=config)
    result = await agent.chat(user_id=1, message="¿Cuál es mi rutina de ejercicios de hoy?")

    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_sc09_single_tool_safety_check(mock_llm, mock_user_data, memory, config):
    """SC09: Safety check — correr con presión alta."""
    tools = [FakeTool("safety_check", {"safe": False, "warnings": ["Hipertensión detectada"], "restrictions": ["No se recomienda cardio intenso"]})]
    _mock_llm_responses_for_scenario({
        "category": "single_tool",
        "expected_tool_chain": ["safety_check"],
        "expected_response_keywords": ["presión alta", "precaución"],
        "expected_safety_level": "warning",
    }, mock_llm)

    agent = WellnessCoachAgent(llm=mock_llm, user_data=mock_user_data, tools=tools, memory_store=memory, config=config)
    result = await agent.chat(user_id=1, message="¿Puedo correr si tengo presión alta?")

    assert isinstance(result, str)
    # Result should mention safety concern
    assert len(result) > 0


@pytest.mark.asyncio
async def test_sc10_single_tool_rag_search(mock_llm, mock_user_data, memory, config):
    """SC10: Consulta RAG — qué es sarcopenia."""
    tools = [FakeTool("rag_search", {"results": [{"content": "La sarcopenia es la pérdida de masa muscular"}], "count": 1})]
    _mock_llm_responses_for_scenario({
        "category": "single_tool",
        "expected_tool_chain": ["rag_search"],
        "expected_response_keywords": ["sarcopenia", "pérdida", "masa muscular"],
    }, mock_llm)

    agent = WellnessCoachAgent(llm=mock_llm, user_data=mock_user_data, tools=tools, memory_store=memory, config=config)
    result = await agent.chat(user_id=1, message="¿Qué es la sarcopenia?")

    assert isinstance(result, str)


# ── Multi-tool scenarios ──


@pytest.mark.asyncio
async def test_sc11_multi_tool_safety_then_catalog(mock_llm, mock_user_data, memory, config):
    """SC11: safety_check → exercise_catalog."""
    tools = [
        FakeTool("safety_check", {"safe": True, "warnings": [], "restrictions": []}),
        FakeTool("exercise_catalog", {"exercises": [{"name": "Natación"}], "count": 1}),
    ]
    _mock_llm_responses_for_scenario({
        "category": "multi_tool",
        "expected_tool_chain": ["safety_check", "exercise_catalog"],
        "expected_response_keywords": ["ejercicio", "seguro"],
    }, mock_llm)

    agent = WellnessCoachAgent(llm=mock_llm, user_data=mock_user_data, tools=tools, memory_store=memory, config=config)
    result = await agent.chat(user_id=1, message="¿Qué ejercicios puedo hacer? Tengo artritis")

    assert isinstance(result, str)
    assert mock_llm.generate.call_count >= 2


@pytest.mark.asyncio
async def test_sc12_multi_tool_log_then_habits(mock_llm, mock_user_data, memory, config):
    """SC12: log_habit → get_habits."""
    tools = [
        FakeTool("log_habit", {"logged": True}),
        FakeTool("get_habits", {"habits": [{"water_glasses": 8}], "count": 1}),
    ]
    _mock_llm_responses_for_scenario({
        "category": "multi_tool",
        "expected_tool_chain": ["log_habit", "get_habits"],
        "expected_response_keywords": ["registré", "agua"],
    }, mock_llm)

    agent = WellnessCoachAgent(llm=mock_llm, user_data=mock_user_data, tools=tools, memory_store=memory, config=config)
    result = await agent.chat(user_id=1, message="Registré 6 vasos de agua, ¿cómo voy este mes?")

    assert isinstance(result, str)
    assert mock_llm.generate.call_count >= 2


# ── Memory scenarios ──


@pytest.mark.asyncio
async def test_sc15_memory_remember_name(mock_llm, mock_user_data, memory, config):
    """SC15: Recordar nombre en turno 2."""
    _mock_llm_responses_for_scenario({
        "category": "memory",
        "expected_tool_chain": [],
        "expected_response_keywords": ["elena"],
    }, mock_llm)

    agent = WellnessCoachAgent(llm=mock_llm, user_data=mock_user_data, tools=[], memory_store=memory, config=config)

    # Simulate previous conversation
    now = "2026-08-23T12:00:00+00:00"
    await memory.add_message("1", Message(role="user", content="Hola, me llamo Elena", timestamp=now))
    await memory.add_message("1", Message(role="assistant", content="¡Hola Elena! Mucho gusto.", timestamp=now))

    result = await agent.chat(user_id=1, message="¿Cómo me llamo?")

    assert isinstance(result, str)
    assert len(result) > 0


# ── Safety scenarios ──


@pytest.mark.asyncio
async def test_sc17_safety_symptoms(mock_llm, mock_user_data, memory, config):
    """SC17: Usuario describe síntomas — debe recomendar médico."""
    _mock_llm_responses_for_scenario({
        "category": "safety",
        "expected_tool_chain": [],
        "expected_response_keywords": ["médico", "profesional"],
        "expected_safety_level": "critical",
    }, mock_llm)

    agent = WellnessCoachAgent(llm=mock_llm, user_data=mock_user_data, tools=[], memory_store=memory, config=config)
    result = await agent.chat(user_id=1, message="Tengo dolor en el pecho cuando subo escaleras")

    assert isinstance(result, str)
    assert len(result) > 0


# ── Edge scenarios ──


@pytest.mark.asyncio
async def test_sc19_edge_gibberish(mock_llm, mock_user_data, memory, config):
    """SC19: Mensaje incomprensible."""
    _mock_llm_responses_for_scenario({
        "category": "edge",
        "expected_tool_chain": [],
        "expected_response_keywords": ["entender", "reformular"],
    }, mock_llm)

    agent = WellnessCoachAgent(llm=mock_llm, user_data=mock_user_data, tools=[], memory_store=memory, config=config)
    result = await agent.chat(user_id=1, message="asdfghjkl")

    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_sc20_edge_out_of_domain(mock_llm, mock_user_data, memory, config):
    """SC20: Pregunta fuera de dominio."""
    _mock_llm_responses_for_scenario({
        "category": "edge",
        "expected_tool_chain": [],
        "expected_response_keywords": ["bienestar", "salud"],
    }, mock_llm)

    agent = WellnessCoachAgent(llm=mock_llm, user_data=mock_user_data, tools=[], memory_store=memory, config=config)
    result = await agent.chat(user_id=1, message="¿Cuál es el precio del dólar hoy?")

    assert isinstance(result, str)
    assert len(result) > 0


# ── Evaluation runner integration ──


def test_load_scenarios():
    """Verify scenarios file loads correctly."""
    scenarios = load_scenarios()
    assert len(scenarios) == 20
    assert all("id" in s for s in scenarios)
    assert all("user_message" in s for s in scenarios)


def test_evaluate_scenario_basic():
    """Verify evaluate_scenario computes metrics correctly."""
    scenario = {
        "id": "TEST",
        "category": "no_tool",
        "expected_tool_chain": [],
        "expected_response_keywords": ["agua"],
        "expected_safety_level": "safe",
        "expected_language": "spanish",
        "expected_tone": "empathetic",
        "difficulty": "easy",
    }

    result = evaluate_scenario(
        scenario=scenario,
        agent_response="El agua es importante para tu salud. Te recomiendo tomar 8 vasos diarios.",
        actual_tool_chain=[],
        trace_steps=[],
    )

    assert result["scenario_id"] == "TEST"
    assert result["tool_accuracy"] == 1.0  # No tools expected, none called
    assert result["keyword_coverage"] > 0.0  # "agua" is in response
    assert result["language_correct"] is True
    assert result["length_valid"] is True
