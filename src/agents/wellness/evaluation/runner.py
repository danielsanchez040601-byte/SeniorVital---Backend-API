"""Coach Agent evaluation runner.

Orchestrates scenario execution, metric computation, and report generation.
Supports both mock (CI) and real (manual validation) modes.
"""

from __future__ import annotations

import json
import logging
import statistics
from pathlib import Path
from typing import Any

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
from src.agents.wellness.evaluation.quality import context_coherence, memory_retention

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "evaluation"
SCENARIOS_FILE = DATA_DIR / "coach_scenarios.json"


def load_scenarios(path: Path | None = None) -> list[dict[str, Any]]:
    """Load evaluation scenarios from JSON file.

    Args:
        path: Path to scenarios file. Defaults to coach_scenarios.json.

    Returns:
        List of scenario dicts.
    """
    path = path or SCENARIOS_FILE
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("scenarios", [])


def evaluate_scenario(
    scenario: dict[str, Any],
    agent_response: str,
    actual_tool_chain: list[str],
    trace_steps: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Evaluate a single scenario against expected outcomes.

    Args:
        scenario: The scenario definition.
        agent_response: The agent's text response.
        actual_tool_chain: Tools that were actually called.
        trace_steps: ReAct trace steps (optional).

    Returns:
        Dict with per-metric results.
    """
    expected_tools = scenario.get("expected_tool_chain", [])
    expected_keywords = scenario.get("expected_response_keywords", [])
    expected_safety = scenario.get("expected_safety_level", "safe")
    expected_language = scenario.get("expected_language", "spanish")
    expected_tone = scenario.get("expected_tone", "empathetic")

    # Tool metrics
    tool_accuracy = tool_selection_accuracy(expected_tools, actual_tool_chain)
    tool_completeness = tool_chain_completeness(expected_tools, actual_tool_chain)
    unnecessary = unnecessary_tool_calls(expected_tools, actual_tool_chain)

    # ReAct flow validity
    react_validity = react_flow_validity(trace_steps or [])

    # Safety
    safety = safety_compliance(agent_response, expected_safety)

    # Language
    lang = language_check(agent_response, expected_language)

    # Tone
    tone = tone_check(agent_response, expected_tone)

    # Length
    length = response_length_check(agent_response)

    # Keyword coverage (reuse from RAG metrics)
    from src.rag.evaluation.quality import keyword_coverage

    kw_coverage = keyword_coverage(agent_response, expected_keywords)

    return {
        "scenario_id": scenario["id"],
        "category": scenario.get("category", "unknown"),
        "difficulty": scenario.get("difficulty", "medium"),
        "tool_accuracy": tool_accuracy,
        "tool_completeness": tool_completeness,
        "unnecessary_tool_calls": unnecessary,
        "react_valid": react_validity["valid"],
        "react_issues": react_validity["issues"],
        "safety_compliant": safety["compliant"],
        "safety_detected": safety["detected_level"],
        "language_correct": lang["correct"],
        "tone_matches": tone["matches"],
        "tone_detected": tone["detected_tone"],
        "length_valid": length["valid"],
        "word_count": length["word_count"],
        "keyword_coverage": kw_coverage,
        "response": agent_response,
        "actual_tool_chain": actual_tool_chain,
    }


def compute_aggregate_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute aggregate metrics from individual scenario results.

    Args:
        results: List of per-scenario evaluation results.

    Returns:
        Dict with aggregated metrics and per-category breakdowns.
    """
    if not results:
        return {"error": "No results to evaluate"}

    # Filter out errored results
    valid = [r for r in results if "error" not in r]
    if not valid:
        return {"error": "No valid results"}

    # Aggregate metrics
    tool_accuracies = [r["tool_accuracy"] for r in valid]
    kw_coverages = [r["keyword_coverage"] for r in valid]
    safety_complies = [r["safety_compliant"] for r in valid]
    react_valids = [r["react_valid"] for r in valid]
    tone_matches = [r["tone_matches"] for r in valid]
    word_counts = [r["word_count"] for r in valid]

    # Per-category breakdown
    categories = {}
    for r in valid:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r)

    per_category = {}
    for cat, cat_results in categories.items():
        per_category[cat] = {
            "count": len(cat_results),
            "avg_tool_accuracy": round(
                statistics.mean([r["tool_accuracy"] for r in cat_results]), 2
            ),
            "avg_keyword_coverage": round(
                statistics.mean([r["keyword_coverage"] for r in cat_results]), 2
            ),
            "safety_compliance_rate": round(
                sum(1 for r in cat_results if r["safety_compliant"]) / len(cat_results), 2
            ),
            "tone_match_rate": round(
                sum(1 for r in cat_results if r["tone_matches"]) / len(cat_results), 2
            ),
        }

    # Per-difficulty breakdown
    difficulties = {}
    for r in valid:
        diff = r["difficulty"]
        if diff not in difficulties:
            difficulties[diff] = []
        difficulties[diff].append(r)

    per_difficulty = {}
    for diff, diff_results in difficulties.items():
        per_difficulty[diff] = {
            "count": len(diff_results),
            "avg_tool_accuracy": round(
                statistics.mean([r["tool_accuracy"] for r in diff_results]), 2
            ),
            "avg_keyword_coverage": round(
                statistics.mean([r["keyword_coverage"] for r in diff_results]), 2
            ),
        }

    # Word count stats
    wc_stats = {
        "min": min(word_counts),
        "max": max(word_counts),
        "mean": round(statistics.mean(word_counts), 1),
        "median": round(statistics.median(word_counts), 1),
    }

    return {
        "total_scenarios": len(results),
        "valid_scenarios": len(valid),
        "errored_scenarios": len(results) - len(valid),
        "overall": {
            "avg_tool_accuracy": round(statistics.mean(tool_accuracies), 2),
            "avg_keyword_coverage": round(statistics.mean(kw_coverages), 2),
            "safety_compliance_rate": round(sum(safety_complies) / len(valid), 2),
            "react_validity_rate": round(sum(react_valids) / len(valid), 2),
            "tone_match_rate": round(sum(tone_matches) / len(valid), 2),
            "avg_word_count": wc_stats["mean"],
            "word_count_stats": wc_stats,
        },
        "per_category": per_category,
        "per_difficulty": per_difficulty,
    }


def save_results(
    results: list[dict[str, Any]],
    metrics: dict[str, Any],
    output_dir: Path | None = None,
) -> tuple[Path, Path]:
    """Save evaluation results and metrics to JSON files.

    Args:
        results: Per-scenario results.
        metrics: Aggregated metrics.
        output_dir: Output directory. Defaults to data/evaluation/coach_results/.

    Returns:
        Tuple of (raw_results_path, metrics_summary_path).
    """
    output_dir = output_dir or DATA_DIR / "coach_results"
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_path = output_dir / "raw_results.json"
    metrics_path = output_dir / "metrics_summary.json"

    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    logger.info(f"Results saved to {raw_path}")
    logger.info(f"Metrics saved to {metrics_path}")

    return raw_path, metrics_path
