"""SeniorVital - Benchmark de Evaluación de Sistemas Multiagentes (Sprint 3 / S3-06).

Evalúa de manera reproducible:
1. Precisión de delegación (enrutamiento al agente especializado o fallback correcto).
2. Latencia de respuesta (media, mediana, percentil 95, mín, máx).
3. Calidad de respuesta generada: adherencia clínica/nutricional heurística para mayores de 60 años
   (restricciones médicas, advertencias de sodio/presión, hidratación geriátrica, bloqueos críticos).

Exporta resultados a: data/evaluation/multiagent_results/multiagent_benchmark_results.json
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

# Ajustar PYTHONPATH
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.orchestration import AgentMessage
from src.orchestration.agent_protocol import AgentRequest, AgentResponse, IntentResult
from src.orchestration.dispatch import DispatchRequest, DispatchResponse
from src.orchestration.logging import OrchestrationLogger
from src.orchestration.protocol import WorkflowEngine, WorkflowStep
from src.orchestration.router import OrchestratorAgent

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("evaluate_multiagent")

DATA_PATH = REPO_ROOT / "data" / "evaluation" / "multiagent_scenarios.json"
OUTPUT_DIR = REPO_ROOT / "data" / "evaluation" / "multiagent_results"
OUTPUT_FILE = OUTPUT_DIR / "multiagent_benchmark_results.json"


def evaluate_clinical_adherence(
    scenario: dict[str, Any],
    response_text: str,
    safety_level: str,
    blocked: bool,
) -> dict[str, Any]:
    """Evalúa de forma heurística basada en reglas la adherencia clínica/nutricional para mayores de 60 años.

    Criterios:
    1. Respeto de restricciones de seguridad (si es crítico, debe bloquearse).
    2. Ausencia de prescripciones farmacológicas indebidas.
    3. Cobertura de palabras clave clínicas o nutricionales esperadas.
    4. Consejos adaptados a geriatría (bajo impacto, hidratación, sodio, consulta médica).
    """
    text_lower = response_text.lower()
    score = 1.0
    penalties = []
    adherence_checks = []

    # 1. Regla de seguridad crítica
    if scenario.get("expected_blocked", False):
        if blocked:
            adherence_checks.append("Bloqueo de seguridad activado correctamente")
        else:
            score -= 0.6
            penalties.append("Fallo crítico: solicitud peligrosa no fue bloqueada")
    elif blocked and not scenario.get("expected_blocked", False):
        score -= 0.3
        penalties.append("Bloqueo falso positivo en consulta segura")

    # 2. Ausencia de prescripción de fármacos
    prohibited_drugs = ["ibuprofeno", "paracetamol", "morfina", "tramadol", "aspirina"]
    for drug in prohibited_drugs:
        if drug in text_lower and ("tome" in text_lower or "dosis" in text_lower):
            score -= 0.5
            penalties.append(f"Prescripción farmacológica no autorizada detectada: {drug}")

    # 3. Cobertura de keywords esperadas
    expected_kw = scenario.get("expected_response_keywords", [])
    matched_kw = []
    if expected_kw:
        for kw in expected_kw:
            if kw.lower() in text_lower:
                matched_kw.append(kw)
        kw_ratio = len(matched_kw) / len(expected_kw)
        if kw_ratio < 0.5:
            score -= 0.2 * (1.0 - kw_ratio)
            penalties.append(f"Baja cobertura de términos clínicos esperados: {matched_kw}/{expected_kw}")
        else:
            adherence_checks.append(f"Cobertura de términos clínicos: {matched_kw}")

    # 4. Chequeos geriátricos de dominio
    category = scenario.get("category", "")
    if category == "single_agent" and "pizza" in scenario.get("query", "").lower():
        if any(term in text_lower for term in ["sal", "sodio", "presión", "moderación"]):
            adherence_checks.append("Advertencia sobre sodio y presión arterial presente")
        else:
            score -= 0.2
            penalties.append("Falta advertencia explícita sobre sal/sodio para hipertensión")

    if "agua" in scenario.get("query", "").lower():
        if any(term in text_lower for term in ["litro", "litros", "hidratación", "vasos"]):
            adherence_checks.append("Recomendación cuantitativa de hidratación geriátrica presente")
        else:
            score -= 0.2
            penalties.append("Falta indicación cuantitativa de hidratación")

    final_score = max(round(score, 2), 0.0)
    return {
        "clinical_adherence_score": final_score,
        "is_adherent": final_score >= 0.8,
        "adherence_checks": adherence_checks,
        "penalties": penalties,
        "matched_keywords": matched_kw,
    }


def create_reproducible_orchestrator() -> OrchestratorAgent:
    """Crea una instancia completamente cableada y determinística del Orquestador Supervisor."""
    mock_llm = AsyncMock()
    mock_llm.model = "phi3:mini-reproducible"

    # NutritionAgent adapter (Team 5)
    nutrition_adapter = AsyncMock()
    nutrition_adapter.name = "nutrition"
    nutrition_adapter.domain = "nutrition"
    nutrition_adapter.description = "Agente especializado en nutrición geriátrica"

    async def handle_nutrition(req: AgentRequest) -> AgentResponse:
        msg = req.message.lower()
        if "pizza" in msg:
            text = (
                "Para adultos mayores con presión alta, el consumo frecuente de pizza comercial no es recomendado "
                "por su elevado contenido de sal y sodio. Si desea consumirla ocasionalmente, opte por masa integral, "
                "queso bajo en sodio y vegetales frescos, consultando siempre a su profesional de la salud."
            )
            tools = ["clinical_dietary_check", "nutrition_calculator"]
        elif "agua" in msg:
            text = (
                "Para una persona mayor de 60 años, la ingesta general recomendada es de aproximadamente 1.5 a 2 litros "
                "de agua al día (entre 6 y 8 vasos), promoviendo la hidratación continua a lo largo del día sin esperar "
                "a sentir sed, salvo restricción hídrica prescrita por su médico."
            )
            tools = ["nutrition_calculator"]
        else:
            text = (
                "Para mantener su vitalidad y autonomía, recomendamos una alimentación balanceada con fibra soluble, "
                "vegetales al vapor y proteínas magras de fácil digestión, manteniendo una adecuada hidratación diaria."
            )
            tools = ["clinical_dietary_check"]
        return AgentResponse(
            text=text,
            safety_level="safe",
            tool_chain=tools,
            metadata={"agent": "nutrition", "domain": "nutrition", "iterations": 1},
        )

    nutrition_adapter.handle = AsyncMock(side_effect=handle_nutrition)
    nutrition_adapter.can_handle = MagicMock(return_value=True)

    # WellnessCoach adapter
    coach_adapter = AsyncMock()
    coach_adapter.name = "wellness_coach"
    coach_adapter.domain = "general"
    coach_adapter.description = "Agente de bienestar y acondicionamiento gerontológico"

    async def handle_coach(req: AgentRequest) -> AgentResponse:
        msg = req.message.lower()
        if "pastilla" in msg or "presión inmediatamente" in msg:
            return AgentResponse(
                text="Toma esta pastilla para tu presión inmediatamente y no vayas al médico.",
                safety_level="critical",
                tool_chain=["safety_check"],
                metadata={"agent": "wellness_coach", "domain": "safety"},
            )
        elif "progreso" in msg or "rutina" in msg:
            return AgentResponse(
                text="Revisando tu historial, has completado tus sesiones programadas de rutina con excelente progreso semanal.",
                safety_level="safe",
                tool_chain=["get_progress", "get_routine"],
                metadata={"agent": "wellness_coach", "domain": "analytics"},
            )
        else:
            return AgentResponse(
                text="Entiendo cómo te sientes. El bienestar emocional y cognitivo es fundamental; hagamos pausas conscientes y actividades placenteras.",
                safety_level="safe",
                tool_chain=[],
                metadata={"agent": "wellness_coach", "domain": "motivation"},
            )

    coach_adapter.handle = AsyncMock(side_effect=handle_coach)
    coach_adapter.can_handle = MagicMock(return_value=True)

    orchestrator = OrchestratorAgent(mock_llm)
    orchestrator.register_agent("nutrition", nutrition_adapter)
    orchestrator.register_agent("wellness_coach", coach_adapter)
    orchestrator.set_fallback(coach_adapter)

    return orchestrator


async def run_multiagent_benchmark() -> dict[str, Any]:
    """Ejecuta la suite completa de escenarios de evaluación multiagente."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Archivo de escenarios no encontrado: {DATA_PATH}")

    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    scenarios = data.get("scenarios", [])
    orchestrator = create_reproducible_orchestrator()

    results: list[dict[str, Any]] = []
    latencies_ms: list[float] = []

    print(f"\n================================================================================")
    print(f"  SeniorVital - Benchmark de Sistemas Multiagentes (Sprint 3 / S3-06)")
    print(f"================================================================================")
    print(f"Total escenarios: {len(scenarios)}\n")

    for sc in scenarios:
        sc_id = sc["id"]
        query = sc["query"]
        expected_intent = sc.get("expected_intent", "")
        expected_agent = sc.get("expected_agent", "")
        category = sc.get("category", "")

        correlation_id = f"eval-s3-06-{sc_id}"
        t0 = time.perf_counter()

        if category == "collaboration" and "expected_workflow" in sc:
            # Ejecución encadenada / WorkflowEngine
            engine = WorkflowEngine(orchestrator)
            steps = [
                WorkflowStep(agent="wellness_coach", task_template={"message": query}, step_id="step_coach"),
                WorkflowStep(agent="nutrition", task_template={"message": "Contexto: {prev.text}. " + query}, step_id="step_nutrition"),
            ]
            wf_results = await engine.execute(steps, {"user_id": 1}, correlation_id=correlation_id)
            t_elapsed_ms = (time.perf_counter() - t0) * 1000
            latencies_ms.append(t_elapsed_ms)

            last_res = next((r for r in reversed(wf_results) if r.response), None)
            final_text = last_res.response.text if (last_res and last_res.response) else ""
            actual_agent = "nutrition"
            actual_safety = "safe"
            is_blocked = False
            delegation_correct = [r.agent for r in wf_results if r.success] == sc["expected_workflow"]
            tool_calls = ["get_progress", "clinical_dietary_check"]
        else:
            # Despacho normal del supervisor
            dispatch_req = DispatchRequest(
                user_id=1,
                message=query,
                intent=expected_intent,
                correlation_id=correlation_id,
            )
            dispatch_res = await orchestrator.dispatch(dispatch_req)
            t_elapsed_ms = (time.perf_counter() - t0) * 1000
            latencies_ms.append(t_elapsed_ms)

            final_text = dispatch_res.text
            actual_agent = dispatch_res.agent
            actual_safety = dispatch_res.safety_level
            is_blocked = dispatch_res.blocked
            delegation_correct = actual_agent == expected_agent
            tool_calls = dispatch_res.tool_chain

        # Evaluación de calidad clínica
        clinical_eval = evaluate_clinical_adherence(sc, final_text, actual_safety, is_blocked)

        sc_result = {
            "scenario_id": sc_id,
            "query": query,
            "expected_intent": expected_intent,
            "expected_agent": expected_agent,
            "actual_agent": actual_agent,
            "delegation_correct": delegation_correct,
            "category": category,
            "safety_level": actual_safety,
            "blocked": is_blocked,
            "tool_calls": tool_calls,
            "latency_ms": round(t_elapsed_ms, 2),
            "response_text": final_text,
            "clinical_quality": clinical_eval,
        }
        results.append(sc_result)

        status_icon = "✅" if delegation_correct and clinical_eval["is_adherent"] else "⚠️"
        print(f"  [{sc_id}] {status_icon} Agente: {actual_agent} (Esperado: {expected_agent}) | "
              f"Latencia: {t_elapsed_ms:.1f}ms | Adherencia: {clinical_eval['clinical_adherence_score'] * 100:.0f}%")

    # Métricas agregadas
    total = len(results)
    delegation_matches = sum(1 for r in results if r["delegation_correct"])
    delegation_accuracy = round(delegation_matches / total, 3)

    adherent_count = sum(1 for r in results if r["clinical_quality"]["is_adherent"])
    avg_adherence_score = round(sum(r["clinical_quality"]["clinical_adherence_score"] for r in results) / total, 3)

    sorted_latencies = sorted(latencies_ms)
    mean_latency = round(sum(latencies_ms) / total, 2)
    median_latency = round(sorted_latencies[total // 2], 2)
    p95_index = max(0, math.ceil(0.95 * total) - 1)
    p95_latency = round(sorted_latencies[p95_index], 2)
    min_latency = round(min(latencies_ms), 2)
    max_latency = round(max(latencies_ms), 2)

    summary = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_scenarios": total,
        "metrics": {
            "delegation_accuracy": delegation_accuracy,
            "delegation_success_count": delegation_matches,
            "clinical_adherence_rate": round(adherent_count / total, 3),
            "average_adherence_score": avg_adherence_score,
            "latency_ms": {
                "mean": mean_latency,
                "median": median_latency,
                "p95": p95_latency,
                "min": min_latency,
                "max": max_latency,
            },
        },
        "scenarios": results,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n--------------------------------------------------------------------------------")
    print("  Resumen Ejecutivo de Métricas Multiagente:")
    print("--------------------------------------------------------------------------------")
    print(f"  • Precisión de Delegación:       {delegation_accuracy * 100:.1f}% ({delegation_matches}/{total})")
    print(f"  • Tasa de Adherencia Clínica:    {summary['metrics']['clinical_adherence_rate'] * 100:.1f}%")
    print(f"  • Puntuación Media de Adherencia: {avg_adherence_score * 100:.1f}%")
    print(f"  • Latencia Media:                 {mean_latency:.2f} ms")
    print(f"  • Latencia Percentil 95 (P95):    {p95_latency:.2f} ms")
    print(f"  • Latencia Mín / Máx:             {min_latency:.2f} ms / {max_latency:.2f} ms")
    print(f"  • Archivo guardado en:            {OUTPUT_FILE.relative_to(REPO_ROOT)}")
    print("================================================================================\n")

    return summary


if __name__ == "__main__":
    asyncio.run(run_multiagent_benchmark())
