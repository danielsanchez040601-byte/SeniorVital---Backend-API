"""S3-06 Multi-agent evaluation — reproducible test cases with observability.

Ejecuta los escenarios de data/evaluation/multiagent_scenarios.json contra
agentes reales (mock LLM) y verifica: delegación correcta, colaboración,
safety/critical, tiempos y trazas de eventos.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.orchestration.dispatch import DispatchRequest
from src.orchestration.evaluation import (
    compute_summary,
    evaluate_single_orchestrator,
    evaluate_workflow,
    load_scenarios,
)
from src.orchestration.protocol import WorkflowStep
from src.orchestration.router import OrchestratorAgent

SCENARIOS_FILE = (
    Path(__file__).parent.parent.parent
    / "data"
    / "evaluation"
    / "multiagent_scenarios.json"
)


def make_llm(answers):
    """LLM mock con respuestas ReAct JSON secuenciales."""
    llm = AsyncMock()
    llm.model = "phi3:mini"
    calls = {"n": 0}

    async def generate(prompt, system=None, format_json=False):
        idx = min(calls["n"], len(answers) - 1)
        calls["n"] += 1
        return answers[idx]

    llm.generate = AsyncMock(side_effect=generate)
    return llm


def make_tool(name, description):
    tool = MagicMock()
    tool.name = name
    tool.description = description
    tool.execute = AsyncMock(
        return_value=MagicMock(success=True, data={"ok": True}, error=None, tool_name=name)
    )
    return tool


@pytest.fixture
def wired_orchestrator():
    """Orchestrator con los 2 agentes reales (LLM mock) para evaluación."""
    from src.agents.nutrition.adapter import NutritionAgentAdapter
    from src.agents.nutrition.agent import NutritionAgent
    from src.agents.wellness.coach import WellnessCoachAgent
    from src.agents.wellness.coach_adapter import WellnessCoachAgentAdapter

    coach_llm = make_llm([
        json.dumps({"thought": "Consulta general de progreso.",
                    "final_answer": "Has completado tus rutinas semanales. Buenos progresos."}),
    ])
    nutrition_llm = make_llm([
        json.dumps({"thought": "Consulta nutricional.",
                    "final_answer": "Con presión alta: reduce la sal, prioriza verduras y consulta a tu médico."}),
    ])

    def build_ud(profile, health, prefs):
        ud = AsyncMock()
        data = MagicMock()
        data.profile = profile
        data.health_profile = health
        data.preferences = prefs
        ud.get_user_data = AsyncMock(return_value=data)
        return ud

    coach = WellnessCoachAgent(
        llm=coach_llm,
        user_data=build_ud({"name": "María", "age": 72},
                           {"age": 72}, {}),
        tools=[make_tool("get_progress", "Progreso del usuario")],
    )
    nutrition = NutritionAgent(
        llm=nutrition_llm,
        user_data=build_ud({"name": "María", "age": 72},
                           {"conditions": ["hipertensión"]},
                           {"dietary_restrictions": ["baja en sal"]}),
        tools=[make_tool("rag_search", "Busca en conocimiento nutricional"),
               make_tool("safety_check", "Valida seguridad")],
    )

    orchestrator = OrchestratorAgent(make_llm(["placeholder"]))
    coach_adapter = WellnessCoachAgentAdapter(coach)
    nutrition_adapter = NutritionAgentAdapter(nutrition)
    orchestrator.register_agent("general", coach_adapter)
    orchestrator.register_agent("wellness_coach", coach_adapter)
    orchestrator.register_agent("nutrition", nutrition_adapter)
    orchestrator.set_fallback(coach_adapter)
    return orchestrator


@pytest.fixture
def scenarios():
    return load_scenarios(SCENARIOS_FILE)


class TestScenarioExecutions:
    """Ejecuta los escenarios del JSON y verifica las métricas clave."""

    @pytest.mark.asyncio
    async def test_nutrition_scenario_delegates_correctly(self, wired_orchestrator, scenarios):
        sc = next(s for s in scenarios if s["id"] == "MA01")
        result = await evaluate_single_orchestrator(wired_orchestrator, sc)
        assert result.delegation_correct is True, result.to_dict()
        assert result.agent == "nutrition"
        assert result.error == ""

    @pytest.mark.asyncio
    async def test_fallback_scenario_uses_coach(self, wired_orchestrator, scenarios):
        """MA03: intent analytics sin agente → coach fallback (delegación al fallback)."""
        sc = next(s for s in scenarios if s["id"] == "MA03")
        result = await evaluate_single_orchestrator(wired_orchestrator, sc)
        assert result.agent == "wellness_coach"
        assert result.error == ""

    @pytest.mark.asyncio
    async def test_critical_scenario_blocks_response(self, wired_orchestrator, scenarios):
        """MA05: respuesta médica peligrosa → blocked con safety critical."""
        sc = next(s for s in scenarios if s["id"] == "MA05")
        # El coach con LLM mock no siempre marca critical: verificamos el
        # mecanismo directo del orquestador con un agent que responde critical.
        critical_agent = AsyncMock()
        critical_agent.name = "critical_agent"
        critical_agent.handle = AsyncMock(return_value=MagicMock(
            safety_level="critical",
            text="Toma esta pastilla ahora",
            tool_chain=[],
            metadata={},
        ))
        wired_orchestrator.register_agent("general", critical_agent)
        wired_orchestrator.set_fallback(critical_agent)
        result = await evaluate_single_orchestrator(wired_orchestrator, sc)
        assert result.blocked is True
        assert result.safety_level == "critical"

    @pytest.mark.asyncio
    async def test_collaboration_workflow_delegates_both_agents(
        self, wired_orchestrator, scenarios
    ):
        """MA06: workflow coach → nutrition (colaboración)."""
        sc = next(s for s in scenarios if s["id"] == "MA06")
        steps = [
            WorkflowStep(
                agent="wellness_coach",
                task_template={"message": "¿Cómo va mi rutina?", "user_id": 1},
                step_id="coach",
            ),
            WorkflowStep(
                agent="nutrition",
                task_template={"message": "Consejo alimenticio para: {prev.text}", "user_id": 1},
                step_id="nutrition",
            ),
        ]
        result = await evaluate_workflow(wired_orchestrator, sc, steps)
        assert result.collaboration is True
        assert result.workflow_steps == ["wellness_coach", "nutrition"]
        assert result.delegation_correct is True


class TestObservability:
    """Verifica que las trazas capturen el recorrido de cada solicitud."""

    @pytest.mark.asyncio
    async def test_events_trace_flow(self, wired_orchestrator, scenarios):
        sc = next(s for s in scenarios if s["id"] == "MA01")
        result = await evaluate_single_orchestrator(wired_orchestrator, sc)
        event_names = {e.get("event") for e in result.events}
        assert "dispatch_start" in event_names
        assert "agent_selected" in event_names or "dispatch_end" in event_names
        assert "dispatch_end" in event_names


class TestSummary:
    """Verifica el agregado de métricas para el reporte."""

    def test_compute_summary_aggregates(self, scenarios):
        from src.orchestration.evaluation import ScenarioResult

        results = [
            ScenarioResult(
                scenario_id="MA01", query="a", intent="nutrition",
                agent="nutrition", expected_agent="nutrition",
                delegation_correct=True, duration_ms=100.0,
            ),
            ScenarioResult(
                scenario_id="MA02", query="b", intent="mixed",
                agent="wellness_coach", expected_agent="nutrition",
                delegation_correct=False, duration_ms=50.0,
            ),
        ]
        summary = compute_summary(results)
        assert summary["total_scenarios"] == 2
        assert summary["passed"] == 1
        assert summary["delegation_accuracy"] == 0.5
        assert summary["avg_duration_ms"] == 75.0
