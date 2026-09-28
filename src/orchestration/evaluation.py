"""Multi-agent flow evaluator — S3-06 observability & evaluation.

Ejecuta un conjunto de escenarios reproducibles contra el OrchestratorAgent,
capturando por cada uno:
- agente seleccionado por el orquestador (dispatch/route)
- correctitud de la delegación (agente esperado vs actual)
- colaboración entre agentes (workflow)
- nivel de seguridad y bloqueo
- tiempo de respuesta (ms)
- trazas de eventos (correlation_id → eventos del OrchestrationLogger)

Design: sin LLM real (mock inyectado) para CI reproducibilidad.
"""

from __future__ import annotations

import json
import logging
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_SCENARIOS = (
    Path(__file__).parent.parent.parent / "data" / "evaluation" / "multiagent_scenarios.json"
)


@dataclass
class ScenarioResult:
    """Resultado de la evaluación de un escenario multiagente."""

    scenario_id: str
    query: str
    intent: str
    agent: str = ""
    expected_agent: str = ""
    delegation_correct: bool = False
    safety_level: str = "safe"
    blocked: bool = False
    duration_ms: float = 0.0
    collaboration: bool = False
    workflow_steps: list[str] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "query": self.query,
            "intent": self.intent,
            "agent": self.agent,
            "expected_agent": self.expected_agent,
            "delegation_correct": self.delegation_correct,
            "safety_level": self.safety_level,
            "blocked": self.blocked,
            "duration_ms": round(self.duration_ms, 1),
            "collaboration": self.collaboration,
            "workflow_steps": self.workflow_steps,
            "event_count": len(self.events),
            "events": self.events,
            "error": self.error,
        }


def load_scenarios(path: Path | None = None) -> list[dict[str, Any]]:
    """Carga los escenarios desde el JSON de evaluación."""
    with open(path or DEFAULT_SCENARIOS, encoding="utf-8") as f:
        return json.load(f)["scenarios"]


async def evaluate_single_orchestrator(
    orchestrator: Any,
    scenario: dict[str, Any],
    correlation_id: str | None = None,
) -> ScenarioResult:
    """Evalúa un escenario de agente único vía orchestrator.dispatch().

    Captura: agente seleccionado, delegación correcta, safety, duración y
    traces del OrchestrationLogger (eventos registrados con caplog).

    Returns:
        ScenarioResult con métricas del escenario.
    """
    from src.orchestration.dispatch import DispatchRequest

    cid = correlation_id or f"ma-{scenario['id']}-eval"
    result = ScenarioResult(
        scenario_id=scenario["id"],
        query=scenario["query"],
        intent=scenario.get("expected_intent", ""),
        expected_agent=scenario.get("expected_agent", ""),
        collaboration=bool(scenario.get("expected_workflow")),
    )

    # Recolectar logs de eventos del flujo
    events: list[dict[str, Any]] = []
    _attach_event_sink(orchestrator, events)

    import time
    t0 = time.monotonic()
    try:
        resp = await orchestrator.dispatch(
            DispatchRequest(
                user_id=1,
                message=scenario["query"],
                intent=scenario.get("expected_intent", ""),
                payload={"scenario": scenario["id"]},
                correlation_id=cid,
            )
        )
        result.duration_ms = (time.monotonic() - t0) * 1000
        result.agent = resp.agent
        result.safety_level = resp.safety_level
        result.blocked = resp.blocked
        result.delegation_correct = resp.agent == scenario.get("expected_agent", "")
    except Exception as e:
        result.duration_ms = (time.monotonic() - t0) * 1000
        result.error = str(e)

    result.events = events
    return result


async def evaluate_workflow(
    orchestrator: Any,
    scenario: dict[str, Any],
    steps: list[Any],
    correlation_id: str | None = None,
) -> ScenarioResult:
    """Evalúa un escenario de colaboración vía WorkflowEngine.

    Args:
        orchestrator: OrchestratorAgent con agentes registrados.
        scenario: Definición del escenario.
        steps: Lista de WorkflowStep.
        correlation_id: Id del flujo.

    Returns:
        ScenarioResult con workflow_steps y delegación por agente.
    """
    from src.orchestration.protocol import WorkflowEngine

    cid = correlation_id or f"ma-{scenario['id']}-eval"
    result = ScenarioResult(
        scenario_id=scenario["id"],
        query=scenario["query"],
        intent=scenario.get("expected_intent", ""),
        expected_agent=scenario.get("expected_agent", ""),
        collaboration=True,
    )

    events: list[dict[str, Any]] = []
    _attach_event_sink(orchestrator, events)

    import time
    engine = WorkflowEngine(orchestrator)
    t0 = time.monotonic()
    try:
        results = await engine.execute(steps, {"user_id": 1}, correlation_id=cid)
        result.duration_ms = (time.monotonic() - t0) * 1000
        result.workflow_steps = [r.agent for r in results if r.success and not r.skipped]
        expected_flow = scenario.get("expected_workflow", [])
        result.delegation_correct = result.workflow_steps == expected_flow
        last = next((r for r in reversed(results) if r.response), None)
        if last and last.response:
            result.agent = last.response.metadata.get("agent", last.agent)
            result.safety_level = last.response.safety_level
    except Exception as e:
        result.duration_ms = (time.monotonic() - t0) * 1000
        result.error = str(e)

    result.events = events
    return result


def _attach_event_sink(orchestrator: Any, events: list[dict[str, Any]]) -> None:
    """Sustituye el sink del OrchestrationLogger para capturar eventos.

    Hookea el logger del módulo de orquestación para capturar los
    eventos JSON (route_start, dispatch_start, agent_selected, etc.).
    """
    import logging as _logging

    class _CaptureHandler(_logging.Handler):
        def emit(self, record: _logging.LogRecord) -> None:
            try:
                msg = record.getMessage()
                if msg.startswith("{"):
                    events.append(json.loads(msg))
            except (json.JSONDecodeError, ValueError):
                pass

    handler = _CaptureHandler()
    logger_orch = _logging.getLogger("src.orchestration.logging")
    logger_orch.addHandler(handler)
    logger_orch.setLevel(_logging.INFO)
    # Cleanup on next call: avoid handler leak (single sink per call)
    if not hasattr(logger_orch, "_s3_06_pending"):
        logger_orch._s3_06_pending = handler
    else:
        logger_orch.removeHandler(logger_orch._s3_06_pending)
        logger_orch._s3_06_pending = handler


def compute_summary(results: list[ScenarioResult]) -> dict[str, Any]:
    """Agrega métricas de todos los escenarios para el reporte."""
    if not results:
        return {"error": "No results"}

    passed = [r for r in results if r.delegation_correct and not r.error]
    durations = [r.duration_ms for r in results if r.duration_ms > 0]
    blocked = sum(1 for r in results if r.blocked)
    collaborations = sum(1 for r in results if r.collaboration)

    return {
        "total_scenarios": len(results),
        "passed": len(passed),
        "failed": len(results) - len(passed),
        "delegation_accuracy": round(len(passed) / len(results), 3),
        "avg_duration_ms": round(statistics.mean(durations), 1) if durations else 0.0,
        "max_duration_ms": round(max(durations), 1) if durations else 0.0,
        "min_duration_ms": round(min(durations), 1) if durations else 0.0,
        "blocked_by_safety": blocked,
        "collaboration_scenarios": collaborations,
        "errors": [r.error for r in results if r.error],
    }
