"""S3-04 Collaboration test — real agents chained via WorkflowEngine.

Scenario (S3-04): orchestrator delegates wellness_coach (progreso/rutina)
then nutrition receives {prev.text} and gives contextual dietary advice.

Uses the REAL WellnessCoachAgent + NutritionAgent (with mock LLM), no DB.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agents.nutrition.adapter import NutritionAgentAdapter
from src.agents.nutrition.agent import NutritionAgent
from src.agents.wellness.coach import WellnessCoachAgent
from src.agents.wellness.coach_adapter import WellnessCoachAgentAdapter
from src.orchestration.router import OrchestratorAgent
from src.orchestration.protocol import WorkflowEngine, WorkflowStep


def make_llm(answers):
    """LLM mock que devuelve respuestas ReAct JSON secuencialmente."""
    llm = AsyncMock()
    llm.model = "phi3:mini"
    calls = 0

    async def generate(prompt, system=None, format_json=False):
        nonlocal calls
        idx = min(calls, len(answers) - 1)
        calls += 1
        return answers[idx]

    llm.generate = AsyncMock(side_effect=generate)
    return llm


def make_tool(name, description):
    tool = MagicMock()
    tool.name = name
    tool.description = description
    tool.execute = AsyncMock(return_value=MagicMock(success=True, data={"ok": True}, error=None, tool_name=name))
    return tool


@pytest.fixture
def coach_agent():
    llm = make_llm([
        json.dumps({"thought": "El usuario pide su progreso de rutinas.", "final_answer": "Has completado tus rutinas de la semana. Buenos progresos."}),
    ])
    user_data = AsyncMock()
    data = MagicMock()
    data.profile = {"name": "María", "age": 72}
    data.health_profile = {"age": 72}
    data.preferences = {}
    user_data.get_user_data = AsyncMock(return_value=data)
    tools = [
        make_tool("get_progress", "Consulta el progreso del usuario"),
        make_tool("get_routine", "Obtiene la rutina del día"),
    ]
    return WellnessCoachAgent(llm=llm, user_data=user_data, tools=tools)


@pytest.fixture
def nutrition_agent():
    llm = make_llm([
        json.dumps({"thought": "El usuario pregunta por comida con presión alta.", "final_answer": "Con presión alta evita el exceso de sal y prioriza verduras y granos integrales."}),
    ])
    user_data = AsyncMock()
    data = MagicMock()
    data.profile = {"name": "María", "age": 72}
    data.health_profile = {"conditions": ["hipertensión"]}
    data.preferences = {"dietary_restrictions": ["baja en sal"]}
    user_data.get_user_data = AsyncMock(return_value=data)
    tools = [
        make_tool("rag_search", "Busca en la base de conocimiento nutricional"),
        make_tool("safety_check", "Valida si la recomendación es segura"),
    ]
    return NutritionAgent(llm=llm, user_data=user_data, tools=tools)


@pytest.fixture
def wired_orchestrator(coach_agent, nutrition_agent):
    orchestrator = OrchestratorAgent(make_llm(["placeholder"]))
    coach_adapter = WellnessCoachAgentAdapter(coach_agent)
    nutrition_adapter = NutritionAgentAdapter(nutrition_agent)
    # Spy para inspeccionar la solicitud que recibe el adapter
    nutrition_adapter.handle = AsyncMock(wraps=nutrition_adapter.handle)
    orchestrator.register_agent("general", coach_adapter)
    orchestrator.register_agent("wellness_coach", coach_adapter)
    orchestrator.register_agent("nutrition", nutrition_adapter)
    orchestrator.set_fallback(coach_adapter)
    return orchestrator


@pytest.mark.asyncio
async def test_s3_collaboration_coach_to_nutrition(wired_orchestrator):
    """Workflow S3-04: wellness_coach → nutrition con {prev.text} contextualizado."""
    engine = WorkflowEngine(wired_orchestrator)
    steps = [
        WorkflowStep(
            agent="wellness_coach",
            task_template={"message": "¿Cómo va mi progreso esta semana?", "user_id": 1},
            step_id="coach_step",
        ),
        WorkflowStep(
            agent="nutrition",
            task_template={"message": "Dame un consejo alimenticio para esta rutina: {prev.text}", "user_id": 1},
            step_id="nutrition_step",
        ),
    ]

    results = await engine.execute(steps, {"user_id": 1}, correlation_id="s3collab_01")

    assert len(results) == 2
    assert results[0].success is True
    assert results[0].agent == "wellness_coach"
    assert results[1].success is True
    assert results[1].agent == "nutrition"

    # El paso 2 recibió el texto del paso 1 (colaboración real encadenada)
    nutrition_call = wired_orchestrator._agents["nutrition"].handle.call_args
    nutrition_msg = nutrition_call[0][0].message if nutrition_call else ""
    assert "Has completado tus rutinas" in nutrition_msg


@pytest.mark.asyncio
async def test_s3_dispatch_real_agents_single_agent(wired_orchestrator):
    """dispatch() con agents reales: nutrition para consulta de comida."""
    from src.orchestration.dispatch import DispatchRequest

    resp = await wired_orchestrator.dispatch(
        DispatchRequest(
            user_id=1,
            message="¿Puedo comer pizza con presión alta?",
            intent="nutrition",
            payload={"macrodomain": "E"},
            context={"user_profile": {"age": 72}},
        )
    )
    assert resp.agent == "nutrition"
    assert resp.intent == "nutrition"
    assert "presión alta" in resp.text.lower() or "sal" in resp.text.lower()
    assert resp.blocked is False
