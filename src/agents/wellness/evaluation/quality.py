"""Coach Agent quality heuristics.

Heuristic-based quality checks for memory, coherence, and relevance.
No external LLM judge required.
"""

from __future__ import annotations

import re
from typing import Any


def memory_retention(
    conversation_history: list[dict[str, str]], key_info: list[str]
) -> dict[str, Any]:
    """Check if the agent retains key information from conversation history.

    Args:
        conversation_history: List of {'role': 'user'|'assistant', 'content': str}.
        key_info: List of key terms that should appear in assistant responses.

    Returns:
        Dict with 'retention_rate' (float), 'found' (list[str]), 'missing' (list[str]).
    """
    if not key_info:
        return {"retention_rate": 1.0, "found": [], "missing": []}

    assistant_messages = [
        m["content"].lower() for m in conversation_history if m.get("role") == "assistant"
    ]

    if not assistant_messages:
        return {"retention_rate": 0.0, "found": [], "missing": key_info}

    all_text = " ".join(assistant_messages)

    found = [info for info in key_info if info.lower() in all_text]
    missing = [info for info in key_info if info.lower() not in all_text]

    return {
        "retention_rate": len(found) / len(key_info) if key_info else 1.0,
        "found": found,
        "missing": missing,
    }


def context_coherence(responses: list[str]) -> dict[str, Any]:
    """Check if a sequence of responses is coherent (no contradictions).

    Heuristic: checks for common contradiction patterns and topic drift.

    Args:
        responses: List of agent responses in order.

    Returns:
        Dict with 'coherent' (bool), 'issues' (list[str]).
    """
    issues = []

    if len(responses) < 2:
        return {"coherent": True, "issues": []}

    # Check for contradiction patterns
    contradiction_pairs = [
        (r"puede(?:s)? hacer", r"no (?:debe|puede) hacer"),
        (r"es seguro", r"no es seguro|es peligroso"),
        (r"te recomiendo", r"no te recomiendo"),
        (r"excelente", r"malo|peligroso"),
    ]

    for i in range(len(responses) - 1):
        resp_lower = responses[i].lower()
        next_lower = responses[i + 1].lower()

        for positive, negative in contradiction_pairs:
            if re.search(positive, resp_lower) and re.search(negative, next_lower):
                issues.append(
                    f"Potential contradiction between response {i + 1} and {i + 2}"
                )

    # Check for topic drift (responses should share some vocabulary)
    if len(responses) >= 2:
        words_per_response = [
            set(re.findall(r"\b\w{4,}\b", r.lower())) for r in responses[-3:]
        ]
        if len(words_per_response) >= 2:
            overlap = len(words_per_response[-1] & words_per_response[-2])
            if overlap < 2 and all(len(w) > 0 for w in words_per_response):
                issues.append("Low vocabulary overlap between consecutive responses")

    return {
        "coherent": len(issues) == 0,
        "issues": issues,
    }


def response_relevance(response: str, user_message: str) -> dict[str, Any]:
    """Check if the response is relevant to the user's message.

    Heuristic: checks for vocabulary overlap and domain keywords.

    Returns:
        Dict with 'relevant' (bool), 'overlap_ratio' (float), 'domain_match' (bool).
    """
    wellness_keywords = {
        "ejercicio", "rutina", "agua", "sueño", "dieta", "comida",
        "salud", "bienestar", "descanso", "caminar", "estirar",
        "peso", "corazón", "articulación", "músculo", "fuerza",
        "flexibilidad", "equilibrio", "coordinación", "resistencia",
        "nutrición", "vitamina", "proteína", "calorías",
        "médico", "doctor", "enfermera", "hospital",
        "seguro", "peligro", "riesgo", "precaución",
    }

    user_words = set(re.findall(r"\b\w{4,}\b", user_message.lower()))
    response_words = set(re.findall(r"\b\w{4,}\b", response.lower()))

    # Vocabulary overlap
    overlap = user_words & response_words
    overlap_ratio = len(overlap) / max(len(user_words), 1)

    # Domain match
    domain_words = response_words & wellness_keywords
    domain_match = len(domain_words) >= 2

    # Relevance: either overlap or domain match
    relevant = overlap_ratio >= 0.1 or domain_match

    return {
        "relevant": relevant,
        "overlap_ratio": round(overlap_ratio, 2),
        "domain_match": domain_match,
        "domain_words_found": list(domain_words)[:5],
    }
