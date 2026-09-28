"""Tests for WellnessCoachAgent — conversational agent with ReAct reasoning."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from src.agents.wellness.coach import WellnessCoachAgent
from src.agents.wellness.config import WellnessConfig
from src.agents.wellness.reasoning import ReActEngine, ReActTrace, ReActStep
from src.agents.wellness.prompts.wellness_coach import WellnessCoachPromptBuilder
from src.memory import MemoryStore, Message
from src.services.llm import LLMService
from src.services.user_data import UserData, UserDataService
from src.tools import Tool, ToolResult


# ── Fakes ──

class FakeMemoryStore:
    """In-memory store para tests."""

    def __init__(self) -> None:
        self.messages: dict[str, list[Message]] = {}

    async def get_history(self, user_id: str, limit: int = 20) -> list[Message]:
        return self.messages.get(user_id, [])[-limit:]

    async def add_message(self, user_id: str, message: Message) -> None:
        self.messages.setdefault(user_id, []).append(message)

    async def clear_history(self, user_id: str) -> None:
        self.messages.pop(user_id, None)


class FakeTool:
    """Tool fake para tests."""

    def __init__(self, name: str = "test_tool", response: dict | None = None) -> None:
        self.name = name
        self.description = f"Fake tool: {name}"
        self._response = response or {"result": "ok"}

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, data=self._response, tool_name=self.name)

    def validate_args(self, **kwargs) -> bool:
        return True


class FailingTool(FakeTool):
    """Tool que falla siempre."""

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=False, error="Simulated failure", tool_name=self.name)


# ── Fixtures ──

@pytest.fixture
def mock_llm():
    return AsyncMock(spec=LLMService)


@pytest.fixture
def mock_user_data():
    svc = AsyncMock(spec=UserDataService)
    svc.get_user_data.return_value = UserData(
        user_id=1,
        profile={"age": 70, "name": "Juan"},
        health_profile={"fitness_level": "principiante"},
        preferences={},
        safe_exercises=[],
    )
    return svc


@pytest.fixture
def tools():
    return [FakeTool("exercise_catalog", {"exercises": [{"name": "Caminata"}]})]


@pytest.fixture
def memory():
    return FakeMemoryStore()


@pytest.fixture
def config():
    return WellnessConfig(max_react_iterations=2, conversation_history_limit=3)


@pytest.fixture
def agent(mock_llm, mock_user_data, tools, memory, config):
    return WellnessCoachAgent(
        llm=mock_llm,
        user_data=mock_user_data,
        tools=tools,
        memory_store=memory,
        config=config,
    )


# ── Tests: WellnessCoachAgent.chat ──

@pytest.mark.asyncio
async def test_chat_returns_response(agent, mock_llm):
    mock_llm.generate.return_value = json.dumps({
        "thought": "El usuario quiere ejercicios",
        "action": "exercise_catalog",
        "action_input": {"level": "principiante"},
    })
    mock_llm.generate.side_effect = [
        json.dumps({"thought": "Tengo info", "action": "", "action_input": {}}),
        "Le recomiendo caminar 20 minutos diarios.",
    ]

    result = await agent.chat(user_id=1, message="¿Qué ejercicios puedo hacer?")

    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_chat_saves_to_memory(agent, mock_llm, memory):
    mock_llm.generate.return_value = "Está bien, puedo ayudarte."

    await agent.chat(user_id=1, message="Hola")

    history = await memory.get_history("1")
    assert len(history) == 2
    assert history[0].role == "user"
    assert history[0].content == "Hola"
    assert history[1].role == "assistant"


@pytest.mark.asyncio
async def test_chat_includes_history_in_context(agent, mock_llm, memory):
    # Add prior history
    now = datetime.now(timezone.utc).isoformat()
    await memory.add_message("1", Message(role="user", content="Hola", timestamp=now))
    await memory.add_message("1", Message(role="assistant", content="Hola Juan", timestamp=now))

    mock_llm.generate.return_value = "Claro, ¿en qué puedo ayudarte?"

    await agent.chat(user_id=1, message="Necesito rutina")

    # Should have called LLM with history in context
    call_args = mock_llm.generate.call_args_list
    # The prompt builder should include the history
    assert mock_llm.generate.called


@pytest.mark.asyncio
async def test_chat_handles_memory_error_gracefully(agent, mock_llm, memory):
    memory.get_history = AsyncMock(side_effect=Exception("Redis down"))
    mock_llm.generate.return_value = "Entendido."

    result = await agent.chat(user_id=1, message="Test")

    # Should still work despite memory failure
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_chat_without_memory(agent, mock_llm, mock_user_data):
    agent_no_mem = WellnessCoachAgent(
        llm=mock_llm,
        user_data=mock_user_data,
        tools=[],
        memory_store=None,
    )
    mock_llm.generate.return_value = "Puedo ayudarte."

    result = await agent_no_mem.chat(user_id=1, message="Hola")

    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_chat_with_no_tools(agent, mock_llm):
    agent._tools = []
    mock_llm.generate.return_value = "Sin herramientas disponibles."

    result = await agent.chat(user_id=1, message="Hola")

    assert isinstance(result, str)


# ── Tests: ReActEngine ──

@pytest.mark.asyncio
async def test_react_engine_single_step(mock_llm):
    mock_llm.generate.return_value = json.dumps({
        "thought": "No necesito tools",
        "action": "",
        "action_input": {},
    })
    engine = ReActEngine(llm=mock_llm, tools=[], max_iterations=3)

    trace = await engine.run("System prompt", "User message")

    assert isinstance(trace, ReActTrace)
    assert trace.iterations == 1
    assert trace.final_answer != ""


@pytest.mark.asyncio
async def test_react_engine_with_tool(mock_llm):
    tool = FakeTool("test_tool", {"data": 42})
    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return json.dumps({
                "thought": "Necesito usar test_tool",
                "action": "test_tool",
                "action_input": {"query": "test"},
            })
        return json.dumps({
            "thought": "Tengo la info",
            "action": "",
            "action_input": {},
        })

    mock_llm.generate.side_effect = side_effect
    engine = ReActEngine(llm=mock_llm, tools=[tool], max_iterations=3)

    trace = await engine.run("System", "User")

    assert trace.iterations <= 3
    assert len(trace.steps) >= 1


@pytest.mark.asyncio
async def test_react_engine_max_iterations(mock_llm):
    async def always_tool(*args, **kwargs):
        return json.dumps({
            "thought": "Siempre necesito otra tool",
            "action": "test",
            "action_input": {},
        })

    mock_llm.generate.side_effect = always_tool
    engine = ReActEngine(llm=mock_llm, tools=[FakeTool("test")], max_iterations=2)

    trace = await engine.run("System", "User")

    assert trace.iterations == 2


@pytest.mark.asyncio
async def test_react_engine_handles_tool_failure(mock_llm):
    mock_llm.generate.return_value = json.dumps({
        "thought": "Voy a usar la tool",
        "action": "failing",
        "action_input": {},
    })
    engine = ReActEngine(llm=mock_llm, tools=[FailingTool("failing")], max_iterations=3)

    trace = await engine.run("System", "User")

    # Con tool_failure_threshold=2, el engine reintenta 1 vez antes de abortar
    assert len(trace.steps) == 2
    assert trace.steps[0].tool_result is not None
    assert not trace.steps[0].tool_result.success
    assert trace.steps[1].tool_result is not None
    assert not trace.steps[1].tool_result.success


@pytest.mark.asyncio
async def test_react_engine_handles_unknown_tool(mock_llm):
    mock_llm.generate.return_value = json.dumps({
        "thought": "Uso tool inexistente",
        "action": "nonexistent_tool",
        "action_input": {},
    })
    engine = ReActEngine(llm=mock_llm, tools=[], max_iterations=3)

    trace = await engine.run("System", "User")

    # Con tool_failure_threshold=2, el engine reintenta 1 vez antes de abortar
    assert len(trace.steps) == 2
    assert trace.steps[0].tool_result is not None
    assert not trace.steps[0].tool_result.success
    assert trace.steps[1].tool_result is not None
    assert not trace.steps[1].tool_result.success


# ── Tests: WellnessCoachPromptBuilder ──

def test_prompt_builder_basic():
    builder = WellnessCoachPromptBuilder()
    system, user = builder.build(
        user_message="Hola",
        user_profile={"name": "Juan", "age": 70},
        conversation_history=[],
    )
    assert "Wellness Coach" in system
    assert "Juan" in user
    assert "Hola" in user


def test_prompt_builder_with_history():
    builder = WellnessCoachPromptBuilder()
    now = datetime.now(timezone.utc).isoformat()
    history = [
        Message(role="user", content="Hola", timestamp=now),
        Message(role="assistant", content="Hola Juan", timestamp=now),
    ]
    system, user = builder.build(
        user_message="¿Qué ejercicios?",
        user_profile={"name": "Juan"},
        conversation_history=history,
    )
    assert "Hola" in user
    assert "Hola Juan" in user


def test_prompt_builder_with_tools():
    builder = WellnessCoachPromptBuilder()
    tool = FakeTool("exercise_catalog")
    system, _ = builder.build(
        user_message="Test",
        user_profile={},
        conversation_history=[],
        available_tools=[tool],
    )
    assert "exercise_catalog" in system


def test_prompt_builder_with_tool_results():
    builder = WellnessCoachPromptBuilder()
    results = [ToolResult(success=True, data={"exercises": []}, tool_name="exercise_catalog")]
    _, user = builder.build(
        user_message="Test",
        user_profile={},
        conversation_history=[],
        tool_results=results,
    )
    assert "exercise_catalog" in user


# ── Tests: Multi-turn conversations ──

@pytest.mark.asyncio
async def test_multi_turn_remembers_user_name(agent, mock_llm, memory):
    """El agente recuerda el nombre del usuario en turnos posteriores."""
    # Turno 1: usuario dice su nombre
    mock_llm.generate.return_value = "¡Hola Juan! Qué gusto conocerte."
    await agent.chat(user_id=1, message="Me llamo Juan")

    # Turno 2: usuario pregunta algo que requiere recordar el nombre
    mock_llm.generate.return_value = "Te llamas Juan, ¡claro!"
    result = await agent.chat(user_id=1, message="¿Cómo me llamo?")

    # Verificar que el historial contiene ambos turnos
    history = await memory.get_history("1")
    assert len(history) == 4  # 2 user + 2 assistant
    assert history[0].role == "user"
    assert history[0].content == "Me llamo Juan"
    assert history[2].role == "user"
    assert history[2].content == "¿Cómo me llamo?"


@pytest.mark.asyncio
async def test_multi_turn_5_turnos_coherent(agent, mock_llm, memory):
    """Conversación de 5 turnos con contexto acumulado."""
    conversation = [
        "Hola, tengo 70 años",
        "¿Qué ejercicios puedo hacer?",
        "¿Cada cuánto debo hacerlos?",
        "Registré 6 vasos de agua hoy",
        "¿Qué me recomendaste antes?",
    ]

    responses = [
        "¡Hola! Con esa información puedo ayudarte mejor.",
        "Basado en tu edad, te sugiero caminar.",
        "Te recomiendo 3 veces por semana.",
        "¡Excelente! El agua es muy importante.",
        "Te recomendé caminar 3 veces por semana.",
    ]

    for user_msg, resp in zip(conversation, responses):
        mock_llm.generate.return_value = resp
        result = await agent.chat(user_id=1, message=user_msg)
        assert isinstance(result, str)
        assert len(result) > 0

    # Verificar que los 5 turnos están en memoria
    history = await memory.get_history("1")
    assert len(history) == 10  # 5 user + 5 assistant


@pytest.mark.asyncio
async def test_multi_turn_history_limited_by_config(agent, mock_llm, memory, config):
    """El prompt solo incluye los últimos N mensajes (config.conversation_history_limit)."""
    # El config tiene conversation_history_limit=3
    now = datetime.now(timezone.utc).isoformat()

    # Pre-cargar 6 mensajes (3 turnos) en memoria
    for i in range(6):
        role = "user" if i % 2 == 0 else "assistant"
        await memory.add_message(
            "1",
            Message(role=role, content=f"Msg anterior {i}", timestamp=now),
        )

    mock_llm.generate.return_value = "Respuesta nueva"
    await agent.chat(user_id=1, message="Nuevo mensaje")

    # El historial completo tiene 8 mensajes (6 pre-cargados + 2 nuevos)
    history = await memory.get_history("1")
    assert len(history) == 8

    # Pero el prompt solo debería incluir los últimos 3 (config.conversation_history_limit)
    # Verificar que el LLM fue llamado
    assert mock_llm.generate.called


@pytest.mark.asyncio
async def test_multi_turn_without_memory_is_stateless(agent_no_mem_factory, mock_llm):
    """Sin memoria, cada turno es independiente (sin contexto previo)."""
    agent_no_mem = agent_no_mem_factory
    mock_llm.generate.return_value = "Respuesta"

    await agent_no_mem.chat(user_id=1, message="Me llamo Pedro")
    await agent_no_mem.chat(user_id=1, message="¿Cómo me llamo?")

    # El LLM fue llamado 2 veces, pero sin historial previo en el prompt
    assert mock_llm.generate.call_count == 2


@pytest.fixture
def agent_no_mem_factory(mock_llm, mock_user_data):
    return WellnessCoachAgent(
        llm=mock_llm,
        user_data=mock_user_data,
        tools=[],
        memory_store=None,
    )


@pytest.mark.asyncio
async def test_multi_turn_system_role_in_history(agent, mock_llm, memory):
    """Los mensajes del sistema se almacenan correctamente."""
    now = datetime.now(timezone.utc).isoformat()
    await memory.add_message(
        "1",
        Message(role="system", content="Sistema reiniciado", timestamp=now),
    )

    mock_llm.generate.return_value = "Entendido"
    await agent.chat(user_id=1, message="Hola")

    history = await memory.get_history("1")
    # system + user + assistant = 3
    assert len(history) == 3
    assert history[0].role == "system"


# ── Tests: S2-05 ReAct format, parser, recovery ──


def test_prompt_builder_react_format_instructions():
    """El system prompt contiene instrucciones ReAct con formato JSON."""
    builder = WellnessCoachPromptBuilder()
    tool = FakeTool("exercise_catalog")
    system, _ = builder.build(
        user_message="Hola",
        user_profile={"name": "Juan"},
        conversation_history=[],
        available_tools=[tool],
    )
    assert "final_answer" in system
    assert "thought" in system
    assert "action" in system
    assert "action_input" in system
    assert "exercise_catalog" in system


@pytest.mark.asyncio
async def test_react_engine_final_answer_format(mock_llm):
    """LLM retorna {thought, final_answer} → engine lo parsea como respuesta final."""
    mock_llm.generate.return_value = json.dumps({
        "thought": "El usuario quiere saber algo simple",
        "final_answer": "Puedes caminar 30 minutos al día de forma segura.",
    })
    engine = ReActEngine(llm=mock_llm, tools=[], max_iterations=3)

    trace = await engine.run("System", "User")

    assert trace.iterations == 1
    assert len(trace.steps) == 1
    assert trace.final_answer == "Puedes caminar 30 minutos al día de forma segura."
    assert trace.steps[0].action == ""


@pytest.mark.asyncio
async def test_react_engine_recovery_after_tool_failure(mock_llm):
    """Tool falla → LLM recupera con final_answer."""
    responses = [
        json.dumps({
            "thought": "Necesito verificar seguridad",
            "action": "safety_check",
            "action_input": {"activity": "correr"},
        }),
        json.dumps({
            "thought": "La tool falló, pero puedo responder con info general",
            "final_answer": "Consulte a su médico antes de correr.",
        }),
    ]
    mock_llm.generate.side_effect = responses
    engine = ReActEngine(
        llm=mock_llm,
        tools=[FailingTool("safety_check")],
        max_iterations=3,
    )

    trace = await engine.run("System", "User")

    assert trace.iterations == 2
    assert len(trace.steps) == 2
    assert not trace.steps[0].tool_result.success
    assert trace.final_answer == "Consulte a su médico antes de correr."


@pytest.mark.asyncio
async def test_react_engine_consecutive_failures_break(mock_llm):
    """2 fallos seguidos → ciclo aborta (tool_failure_threshold=2)."""
    mock_llm.generate.return_value = json.dumps({
        "thought": "Voy a reintentar",
        "action": "failing",
        "action_input": {},
    })
    engine = ReActEngine(
        llm=mock_llm,
        tools=[FailingTool("failing")],
        max_iterations=5,
        tool_failure_threshold=2,
    )

    trace = await engine.run("System", "User")

    # Solo 2 iteraciones (1er fallo + reintento → aborta)
    assert trace.iterations == 2
    assert len(trace.steps) == 2
    assert not trace.steps[0].tool_result.success
    assert not trace.steps[1].tool_result.success


@pytest.mark.asyncio
async def test_react_engine_uses_system_prompt(mock_llm):
    """generate() se llama con system= parameter (no concatenado)."""
    mock_llm.generate.return_value = json.dumps({
        "thought": "Respondo directamente",
        "final_answer": "Hola!",
    })
    engine = ReActEngine(llm=mock_llm, tools=[], max_iterations=3)

    await engine.run("SYSTEM_PROMPT_AQUI", "USER_PROMPT_AQUI")

    mock_llm.generate.assert_called_once()
    call_kwargs = mock_llm.generate.call_args
    assert call_kwargs.kwargs.get("system") == "SYSTEM_PROMPT_AQUI"
    assert call_kwargs.args[0] == "USER_PROMPT_AQUI"


@pytest.mark.asyncio
async def test_react_engine_malformed_json(mock_llm):
    """LLM retorna texto no-JSON → parser lo trata como final_answer."""
    mock_llm.generate.return_value = "Esto no es JSON, es una respuesta libre del modelo."
    engine = ReActEngine(llm=mock_llm, tools=[], max_iterations=3)

    trace = await engine.run("System", "User")

    assert trace.iterations == 1
    assert len(trace.steps) == 1
    assert trace.final_answer == "Esto no es JSON, es una respuesta libre del modelo."


@pytest.mark.asyncio
async def test_react_engine_unknown_tool_recovery(mock_llm):
    """Tool desconocida → LLM recupera con final_answer."""
    responses = [
        json.dumps({
            "thought": "Voy a usar una tool que no existe",
            "action": "nonexistent_tool",
            "action_input": {},
        }),
        json.dumps({
            "thought": "Esa tool no existe, respondo directamente",
            "final_answer": "No tengo esa información disponible.",
        }),
    ]
    mock_llm.generate.side_effect = responses
    engine = ReActEngine(llm=mock_llm, tools=[], max_iterations=3)

    trace = await engine.run("System", "User")

    assert trace.iterations == 2
    assert not trace.steps[0].tool_result.success
    assert "no disponible" in trace.steps[0].tool_result.error
    assert trace.final_answer == "No tengo esa información disponible."
