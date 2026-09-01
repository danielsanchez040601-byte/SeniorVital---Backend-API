import pytest
from src.rag.pipeline.rag_pipeline import ClinicalRAGPipeline

def test_rag_pipeline_system_prompt_structure():
    pipeline = ClinicalRAGPipeline()
    context = "PATOLOGÍA: Osteoartritis. Contraindicación: saltos."
    prompt = pipeline.generate_clinical_system_prompt(context)

    assert "SeniorVital" in prompt
    assert "[CONTEXTO CLÍNICO RECUPERADO (RAG)]" in prompt
    assert "Osteoartritis" in prompt
