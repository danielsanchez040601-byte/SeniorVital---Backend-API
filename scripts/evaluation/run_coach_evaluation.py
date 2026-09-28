#!/usr/bin/env python3
"""Coach Agent evaluation CLI.

Usage:
    python scripts/evaluation/run_coach_evaluation.py --mock          # Fast mock evaluation
    python scripts/evaluation/run_coach_evaluation.py --real          # Real Ollama (slow)
    python scripts/evaluation/run_coach_evaluation.py --scenario SC01 # Single scenario
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.agents.wellness.config import WellnessConfig
from src.agents.wellness.evaluation.runner import (
    compute_aggregate_metrics,
    evaluate_scenario,
    load_scenarios,
    save_results,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ── Mock evaluation (fast, for CI) ──


def run_mock_evaluation(scenarios: list[dict]) -> list[dict]:
    """Run evaluation with mock LLM responses."""
    from unittest.mock import AsyncMock, MagicMock

    from src.agents.wellness.coach import WellnessCoachAgent
    from src.tools import Tool, ToolResult

    mock_user_data = AsyncMock()
    mock_user_data.get_user_data.return_value = MagicMock(
        profile={"age": 70, "name": "Carmen", "city": "Madrid"},
        health_profile={"medical_restrictions": ["hipertensión", "artrosis leve"]},
        preferences={},
    )

    tool_responses = {
        "exercise_catalog": {"exercises": [{"name": "Caminata suave", "level": 1}], "count": 1},
        "log_habit": {"logged": True, "type": "water", "value": 8},
        "get_habits": {"habits": [{"date": "2026-08-23", "water_glasses": 8}], "count": 1},
        "get_progress": {"progress": {"adherence": 85}, "insights": ["Buena adherencia"]},
        "get_routine": {"routine": {"exercises": [{"name": "Caminata suave"}]}, "exists": True},
        "safety_check": {"safe": True, "warnings": [], "restrictions": []},
        "rag_search": {"results": [{"content": "Ejercicios de bajo impacto para articulaciones"}], "count": 1},
        "generate_routine": {"routine": {"exercises": [{"name": "Movilidad articular"}]}, "generated": True},
    }

    class EvalFakeTool(Tool):
        def __init__(self, name: str, data: dict):
            self.name = name
            self.description = f"Evaluated tool: {name}"
            self.data = data

        def validate_args(self, **kwargs) -> bool:
            return True

        async def execute(self, **kwargs) -> ToolResult:
            return ToolResult(success=True, data=self.data, tool_name=self.name)

    fake_tools = [EvalFakeTool(name, resp) for name, resp in tool_responses.items()]

    results = []
    for scenario in scenarios:
        expected_chain = scenario.get("expected_tool_chain", [])
        keywords = scenario.get("expected_response_keywords", [])
        safety_level = scenario.get("expected_safety_level", "safe")
        category = scenario.get("category", "no_tool")

        mock_llm = AsyncMock()
        keyword_text = ", ".join(keywords[:2]) if keywords else "bienestar y salud"

        if category == "safety" or safety_level in ("warning", "critical"):
            if expected_chain:
                responses = [
                    json.dumps({
                        "thought": f"Evalúo seguridad y restricciones invocando {expected_chain[0]}.",
                        "action": expected_chain[0],
                        "action_input": {"user_id": 1, "activity": "ejercicio"},
                    }),
                    json.dumps({
                        "thought": "Actividad con posibles riesgos, debo advertir y recomendar consultar a un profesional.",
                        "final_answer": f"Es muy importante que consulte con su médico o profesional de la salud antes de continuar. Su seguridad es primordial respecto a {keyword_text}.",
                    }),
                ]
                mock_llm.generate.side_effect = responses
            else:
                mock_llm.generate.return_value = json.dumps({
                    "thought": "El usuario reporta síntomas o riesgos que ameritan atención médica.",
                    "final_answer": f"Por favor consulte a un médico de forma prioritaria. No soy médico y su seguridad es lo primero en relación a {keyword_text}.",
                })
        elif not expected_chain:
            mock_llm.generate.return_value = json.dumps({
                "thought": "El usuario hace una consulta directa, no requiere herramientas.",
                "final_answer": f"Respuesta orientativa sobre {keyword_text}. Le recomiendo mantener una rutina activa y consultar con un profesional ante cualquier duda.",
            })
        else:
            responses = []
            for tool_name in expected_chain:
                responses.append(
                    json.dumps({
                        "thought": f"Uso {tool_name} para recabar datos clínicos necesarios.",
                        "action": tool_name,
                        "action_input": {"user_id": 1},
                    })
                )
            responses.append(
                json.dumps({
                    "thought": "Toda la información ha sido recopilada con éxito.",
                    "final_answer": f"Con la información obtenida de {', '.join(expected_chain)}, te recomiendo mantener el progreso sobre {keyword_text}.",
                })
            )
            mock_llm.generate.side_effect = responses

        config = WellnessConfig(max_react_iterations=3)
        agent = WellnessCoachAgent(
            llm=mock_llm,
            user_data=mock_user_data,
            tools=fake_tools,
            memory_store=None,
            config=config,
        )

        try:
            start = time.time()
            response, trace = asyncio.run(
                agent.chat_with_trace(user_id=1, message=scenario["user_message"])
            )
            elapsed = time.time() - start

            actual_tool_chain = [s.action for s in trace.steps if s.action]
            trace_steps = [
                {
                    "thought": s.thought,
                    "action": s.action,
                    "tool_result": s.tool_result,
                }
                for s in trace.steps
            ]

            result = evaluate_scenario(
                scenario=scenario,
                agent_response=response,
                actual_tool_chain=actual_tool_chain,
                trace_steps=trace_steps,
            )
            result["elapsed_seconds"] = round(elapsed, 3)
            result["telemetry"] = {
                "mode": "mock_pipeline",
                "iterations": trace.iterations,
                "tools_called": actual_tool_chain,
            }
            results.append(result)
            logger.info(f"  {scenario['id']}: OK ({elapsed:.2f}s)")
        except Exception as e:
            logger.error(f"  {scenario['id']}: ERROR - {e}")
            results.append({
                "scenario_id": scenario["id"],
                "error": str(e),
                "safety_compliant": False,
            })

    return results


# ── Real evaluation (slow, against Ollama) ──


async def run_real_evaluation(scenarios: list[dict]) -> list[dict]:
    """Run evaluation against real Ollama instance."""
    from src.agents.wellness.coach import WellnessCoachAgent
    from src.agents.wellness.reasoning import ReActEngine
    from src.services.llm import LLMService
    from src.services.user_data import UserDataService
    from src.tools.wellness.exercise_catalog import ExerciseCatalogTool
    from src.tools.wellness.get_habits import GetHabitsTool
    from src.tools.wellness.get_progress import GetProgressTool
    from src.tools.wellness.get_routine import GetRoutineTool
    from src.tools.wellness.log_habit import LogHabitTool
    from src.tools.wellness.rag_search import RAGSearchTool
    from src.tools.wellness.safety_check import SafetyCheckTool

    config = WellnessConfig(max_react_iterations=3, llm_timeout=300.0)
    llm = LLMService(base_url=config.llm_url, model=config.llm_model, timeout=config.llm_timeout)

    # Check Ollama health
    healthy = await llm.health_check()
    if not healthy:
        logger.error("Ollama is not available. Start Ollama and try again.")
        return []

    user_data = AsyncMock(spec=UserDataService)
    user_data.get_user_data.return_value = MagicMock(
        profile={"age": 70, "name": "Test"},
        health_profile={"medical_restrictions": []},
        preferences={},
    )

    # Create tools (matching real service wiring)
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:5432/wellness_db")
    db_url_async = db_url.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(db_url_async)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        tools = [
            ExerciseCatalogTool(session),
            GetHabitsTool(session),
            GetProgressTool(session),
            GetRoutineTool(session),
            LogHabitTool(session),
            SafetyCheckTool(session),
            RAGSearchTool(None),
        ]

        results = []
        for scenario in scenarios:
            agent = WellnessCoachAgent(
                llm=llm, user_data=user_data, tools=tools, memory_store=None, config=config
            )

            try:
                start = time.time()
                response = await agent.chat(user_id=1, message=scenario["user_message"])
                elapsed = time.time() - start

                # Extract tool chain from the agent's internal state
                # The agent doesn't expose trace directly, so we track via mock
                actual_tool_chain = []

                result = evaluate_scenario(
                    scenario=scenario,
                    agent_response=response,
                    actual_tool_chain=actual_tool_chain,
                    trace_steps=[],
                )
                result["elapsed_seconds"] = round(elapsed, 2)
                results.append(result)
                logger.info(f"  {scenario['id']}: OK ({elapsed:.2f}s) - {response[:100]}...")
            except Exception as e:
                logger.error(f"  {scenario['id']}: ERROR - {e}")
                results.append({"scenario_id": scenario["id"], "error": str(e)})

    return results


# ── CLI ──


def main():
    parser = argparse.ArgumentParser(description="Coach Agent evaluation")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--mock", action="store_true", help="Run with mock LLM (fast)")
    group.add_argument("--real", action="store_true", help="Run against real Ollama (slow)")
    parser.add_argument("--scenario", type=str, help="Run a single scenario (e.g. SC01)")
    parser.add_argument("--output", type=str, help="Output directory")
    args = parser.parse_args()

    # Load scenarios
    scenarios = load_scenarios()
    if args.scenario:
        scenarios = [s for s in scenarios if s["id"] == args.scenario]
        if not scenarios:
            logger.error(f"Scenario {args.scenario} not found")
            sys.exit(1)

    logger.info(f"Running evaluation: {len(scenarios)} scenarios ({'mock' if args.mock else 'real'} mode)")

    # Run evaluation
    if args.mock:
        results = run_mock_evaluation(scenarios)
    else:
        results = asyncio.run(run_real_evaluation(scenarios))

    # Compute metrics
    metrics = compute_aggregate_metrics(results)

    # Save results
    output_dir = Path(args.output) if args.output else None
    raw_path, metrics_path = save_results(results, metrics, output_dir)

    # Print summary
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total scenarios: {metrics.get('total_scenarios', 0)}")
    print(f"Valid: {metrics.get('valid_scenarios', 0)}")
    print(f"Errored: {metrics.get('errored_scenarios', 0)}")
    print()
    overall = metrics.get("overall", {})
    print(f"Avg Tool Accuracy:     {overall.get('avg_tool_accuracy', 0):.2f}")
    print(f"Avg Keyword Coverage:  {overall.get('avg_keyword_coverage', 0):.2f}")
    print(f"Safety Compliance:     {overall.get('safety_compliance_rate', 0):.2%}")
    print(f"React Validity:        {overall.get('react_validity_rate', 0):.2%}")
    print(f"Tone Match:            {overall.get('tone_match_rate', 0):.2%}")
    print(f"Avg Word Count:        {overall.get('avg_word_count', 0):.0f}")
    print()
    print(f"Raw results: {raw_path}")
    print(f"Metrics:     {metrics_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
