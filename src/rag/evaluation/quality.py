"""Métricas de calidad y adherencia para evaluación clínica RAG y de agentes.
Implementación basada en reglas deterministas y cobertura de palabras clave.
"""

from typing import List


def keyword_coverage(text: str, keywords: List[str]) -> float:
    """Calcula la cobertura de palabras clave clínicas en el texto de respuesta.
    
    Heurística determinista de adherencia clínica basada en palabras clave sin asunciones absolutas.
    """
    if not keywords:
        return 1.0
    if not text:
        return 0.0
    text_lower = text.lower()
    matches = sum(1 for kw in keywords if kw.lower() in text_lower)
    return round(matches / len(keywords), 4)
