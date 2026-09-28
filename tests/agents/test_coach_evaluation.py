"""Coach Agent evaluation metrics tests.

Unit tests for all metric and quality functions in the evaluation module.
"""

import pytest

from src.agents.wellness.evaluation.metrics import (
    language_check,
    react_flow_validity,
    response_length_check,
    safety_compliance,
    tone_check,
    tool_chain_completeness,
    tool_selection_accuracy,
    unnecessary_tool_calls,
)
from src.agents.wellness.evaluation.quality import context_coherence, memory_retention, response_relevance
from src.agents.wellness.evaluation.runner import compute_aggregate_metrics, evaluate_scenario


# ── Tool selection accuracy ──


def test_tool_selection_accuracy_perfect():
    assert tool_selection_accuracy(["A", "B"], ["A", "B"]) == 1.0


def test_tool_selection_accuracy_partial():
    assert tool_selection_accuracy(["A", "B", "C"], ["A", "B"]) == 2 / 3


def test_tool_selection_accuracy_none_expected():
    assert tool_selection_accuracy([], []) == 1.0


def test_tool_selection_accuracy_unnecessary_calls():
    assert tool_selection_accuracy(["A"], ["A", "B"]) == 1.0


def test_tool_selection_accuracy_no_match():
    assert tool_selection_accuracy(["A", "B"], ["C", "D"]) == 0.0


# ── Tool chain completeness ──


def test_tool_chain_completeness_exact():
    assert tool_chain_completeness(["A", "B"], ["A", "B"]) == 1.0


def test_tool_chain_completeness_wrong_order():
    result = tool_chain_completeness(["A", "B"], ["B", "A"])
    assert result < 1.0  # Not perfect due to wrong order


def test_tool_chain_completeness_partial():
    assert tool_chain_completeness(["A", "B", "C"], ["A"]) == 1 / 3


def test_tool_chain_completeness_empty_actual():
    assert tool_chain_completeness(["A", "B"], []) == 0.0


def test_tool_chain_completeness_empty_expected():
    result = tool_chain_completeness([], ["A"])
    assert result < 1.0


# ── Unnecessary tool calls ──


def test_unnecessary_tool_calls_none():
    assert unnecessary_tool_calls(["A", "B"], ["A", "B"]) == 0


def test_unnecessary_tool_calls_some():
    assert unnecessary_tool_calls(["A"], ["A", "B"]) == 1


def test_unnecessary_tool_calls_all_unnecessary():
    assert unnecessary_tool_calls([], ["A", "B"]) == 2


def test_unnecessary_tool_calls_none_called():
    assert unnecessary_tool_calls(["A", "B"], []) == 0


# ── ReAct flow validity ──


def test_react_flow_validity_valid():
    steps = [
        {"thought": "Voy a buscar", "action": "exercise_catalog", "tool_result": {"exercises": []}},
        {"thought": "Tengo la info", "action": "", "tool_result": None},
    ]
    result = react_flow_validity(steps)
    assert result["valid"] is True
    assert result["iteration_count"] == 2


def test_react_flow_validity_missing_thought():
    steps = [
        {"thought": "", "action": "exercise_catalog", "tool_result": {"exercises": []}},
    ]
    result = react_flow_validity(steps)
    assert result["valid"] is False
    assert len(result["issues"]) > 0


def test_react_flow_validity_action_without_result():
    steps = [
        {"thought": "Voy a usar tool", "action": "exercise_catalog", "tool_result": None},
    ]
    result = react_flow_validity(steps)
    assert result["valid"] is False


def test_react_flow_validity_empty():
    result = react_flow_validity([])
    assert result["valid"] is True
    assert result["iteration_count"] == 0


# ── Safety compliance ──


def test_safety_compliance_safe_response():
    result = safety_compliance(
        "Te recomiendo caminar 30 minutos al día.",
        expected_level="safe",
    )
    assert result["compliant"] is True


def test_safety_compliance_warning_detected():
    result = safety_compliance(
        "Ten precaución al hacer ejercicio. No se recomienda intensity sin supervisión.",
        expected_level="warning",
    )
    assert result["compliant"] is True
    assert result["detected_level"] == "warning"


def test_safety_compliance_critical_detected():
    result = safety_compliance(
        "Busque atención médica inmediata. No soy médico, pero esto parece urgente.",
        expected_level="critical",
    )
    assert result["compliant"] is True
    assert result["detected_level"] == "critical"


def test_safety_compliance_missing_warning():
    result = safety_compliance(
        "¡Claro que puedes correr! Es muy saludable.",
        expected_level="warning",
    )
    assert result["compliant"] is False
    assert result["detected_level"] == "safe"


def test_safety_compliance_missing_critical():
    result = safety_compliance(
        "Está bien, puedes hacerlo sin problema.",
        expected_level="critical",
    )
    assert result["compliant"] is False


# ── Language check ──


def test_language_check_spanish():
    result = language_check("El agua es importante para tu salud.", "spanish")
    assert result["correct"] is True
    assert result["confidence"] > 0.3


def test_language_check_english():
    result = language_check("Water is important for your health.", "spanish")
    assert result["correct"] is False


def test_language_check_non_spanish():
    result = language_check("Hello how are you?", "spanish")
    assert result["correct"] is False


# ── Tone check ──


def test_tone_check_empathetic():
    result = tone_check(
        "Excelente, sigue así. Recuerda que el ejercicio es importante para tu salud.",
        "empathetic",
    )
    assert result["matches"] is True
    assert result["detected_tone"] == "empathetic"


def test_tone_check_cautious():
    result = tone_check(
        "Ten precaución. Consulta con tu médico antes de continuar.",
        "cautious",
    )
    assert result["matches"] is True
    assert result["detected_tone"] == "cautious"


def test_tone_check_urgent():
    result = tone_check(
        "Busque atención médica inmediata. Esto es una emergencia.",
        "urgent",
    )
    assert result["matches"] is True
    assert result["detected_tone"] == "urgent"


def test_tone_check_mismatch():
    result = tone_check(
        "Excelente, sigue así.",
        "urgent",
    )
    assert result["matches"] is False


# ── Response length check ──


def test_response_length_check_valid():
    response = " ".join(["palabra"] * 50)
    result = response_length_check(response)
    assert result["valid"] is True
    assert result["word_count"] == 50


def test_response_length_check_too_short():
    result = response_length_check("Hola")
    assert result["valid"] is False


def test_response_length_check_too_long():
    response = " ".join(["palabra"] * 500)
    result = response_length_check(response)
    assert result["valid"] is False


# ── Memory retention ──


def test_memory_retention_found():
    history = [
        {"role": "user", "content": "Me llamo Elena"},
        {"role": "assistant", "content": "Hola Elena, mucho gusto"},
    ]
    result = memory_retention(history, ["Elena"])
    assert result["retention_rate"] == 1.0
    assert "Elena" in result["found"]


def test_memory_retention_missing():
    history = [
        {"role": "user", "content": "Me llamo Elena"},
        {"role": "assistant", "content": "Hola, mucho gusto"},
    ]
    result = memory_retention(history, ["Elena"])
    assert result["retention_rate"] == 0.0
    assert "Elena" in result["missing"]


def test_memory_retention_empty_history():
    result = memory_retention([], ["Elena"])
    assert result["retention_rate"] == 0.0


def test_memory_retention_no_key_info():
    result = memory_retention([], [])
    assert result["retention_rate"] == 1.0


# ── Context coherence ──


def test_context_coherence_coherent():
    responses = [
        "Te recomiendo caminar 30 minutos al día para mantener tu salud.",
        "Caminar es excelente para tu salud cardiovascular y muscular.",
    ]
    result = context_coherence(responses)
    assert result["coherent"] is True


def test_context_coherence_contradiction():
    responses = [
        "Puedes hacer ejercicio sin problema, es seguro.",
        "No debes hacer ejercicio, es peligroso para ti.",
    ]
    result = context_coherence(responses)
    assert result["coherent"] is False


def test_context_coherence_single_response():
    result = context_coherence(["Solo una respuesta"])
    assert result["coherent"] is True


# ── Response relevance ──


def test_response_relevance_relevant():
    result = response_relevance(
        "Te recomiendo caminar para mejorar tu salud.",
        "¿Qué ejercicios puedo hacer?",
    )
    assert result["relevant"] is True


def test_response_relevance_irrelevant():
    result = response_relevance(
        "El precio del dólar hoy es 4000 pesos.",
        "¿Qué ejercicios puedo hacer?",
    )
    assert result["relevant"] is False


# ── Aggregate metrics ──


def test_compute_aggregate_metrics_empty():
    result = compute_aggregate_metrics([])
    assert "error" in result


def test_compute_aggregate_metrics_valid():
    results = [
        {
            "category": "no_tool",
            "difficulty": "easy",
            "tool_accuracy": 1.0,
            "keyword_coverage": 0.8,
            "safety_compliant": True,
            "react_valid": True,
            "tone_matches": True,
            "word_count": 50,
        },
        {
            "category": "single_tool",
            "difficulty": "medium",
            "tool_accuracy": 0.5,
            "keyword_coverage": 0.6,
            "safety_compliant": True,
            "react_valid": True,
            "tone_matches": False,
            "word_count": 80,
        },
    ]
    metrics = compute_aggregate_metrics(results)

    assert metrics["total_scenarios"] == 2
    assert metrics["valid_scenarios"] == 2
    assert metrics["overall"]["avg_tool_accuracy"] == 0.75
    assert "no_tool" in metrics["per_category"]
    assert "single_tool" in metrics["per_category"]
    assert "easy" in metrics["per_difficulty"]
    assert "medium" in metrics["per_difficulty"]


# ── Evaluate scenario ──


def test_evaluate_scenario_tool_chain():
    scenario = {
        "id": "TEST",
        "category": "multi_tool",
        "expected_tool_chain": ["safety_check", "exercise_catalog"],
        "expected_response_keywords": ["ejercicio"],
        "expected_safety_level": "safe",
        "expected_language": "spanish",
        "expected_tone": "empathetic",
        "difficulty": "hard",
    }

    result = evaluate_scenario(
        scenario=scenario,
        agent_response="Te recomiendo estos ejercicios seguros.",
        actual_tool_chain=["safety_check", "exercise_catalog"],
        trace_steps=[
            {"thought": "Verifico seguridad", "action": "safety_check", "tool_result": {"safe": True}},
            {"thought": "Busco ejercicios", "action": "exercise_catalog", "tool_result": {"exercises": []}},
            {"thought": "Respondo", "action": "", "tool_result": None},
        ],
    )

    assert result["tool_accuracy"] == 1.0
    assert result["tool_completeness"] == 1.0
    assert result["unnecessary_tool_calls"] == 0
    assert result["react_valid"] is True
    assert result["keyword_coverage"] > 0.0
