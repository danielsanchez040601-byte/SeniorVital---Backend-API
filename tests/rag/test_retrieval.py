import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.rag.pipeline.rag_pipeline import ClinicalRAGPipeline


def test_rag_pipeline_system_prompt_structure():
    pipeline = ClinicalRAGPipeline()
    context = "PATOLOGÍA: Osteoartritis. Contraindicación: saltos."
    prompt = pipeline.generate_clinical_system_prompt(context)

    assert "SeniorVital" in prompt
    assert "[CONTEXTO CLÍNICO RECUPERADO (RAG)]" in prompt
    assert "Osteoartritis" in prompt


@pytest.mark.asyncio
async def test_rag_pipeline_full_orchestration_with_telemetry():
    """
    Valida la orquestación end-to-end de run_pipeline con mocks deterministas:
    - Simula la recuperación de chunks y telemetría de base vectorial.
    - Simula la inferencia del LLM primario (Google AI Studio).
    - Comprueba la coherencia de retrieved_chunks, context_injected y telemetry.
    """
    mock_chunks = [
        {
            "chunk_id": "OA-01_CONTRA",
            "condition_id": "OA-01",
            "category": "contraindications",
            "content": "Prohibido impacto articular y saltos por riesgo de desgaste.",
            "similarity": 0.9450
        },
        {
            "chunk_id": "OA-01_REC",
            "condition_id": "OA-01",
            "category": "recommended_exercises",
            "content": "Sentadilla asistida en silla con ángulo controlado.",
            "similarity": 0.8920
        }
    ]
    mock_ret_telemetry = {
        "embedding_mode": "HUGGINGFACE_REAL_MODEL",
        "vector_backend": "SUPABASE_PGVECTOR"
    }

    mock_retriever = MagicMock()
    mock_retriever.retrieve_with_telemetry = AsyncMock(return_value=(mock_chunks, mock_ret_telemetry))

    pipeline = ClinicalRAGPipeline(retriever=mock_retriever, similarity_threshold=0.40, top_k=2)

    with patch.object(pipeline, "_call_gemini", return_value="Respuesta clínica simulada: No realice saltos."):
        result = await pipeline.run_pipeline("¿Puedo hacer sentadillas con salto?")

    # Verificaciones de orquestación y estructura del resultado
    assert result["status"] == "SUCCESS"
    assert result["provider"] == "Google AI Studio (Gemini Flash Lite)"
    assert "Respuesta clínica simulada" in result["response"]

    # Verificación de chunks recuperados
    assert isinstance(result["retrieved_chunks"], list)
    assert len(result["retrieved_chunks"]) == 2
    assert result["retrieved_chunks"][0]["chunk_id"] == "OA-01_CONTRA"

    # Verificación de contexto inyectado
    assert "context_injected" in result
    assert "OA-01" in result["context_injected"]
    assert "Prohibido impacto articular" in result["context_injected"]

    # Verificación estricta del objeto de telemetría post-ejecución
    assert "telemetry" in result
    telemetry = result["telemetry"]
    assert telemetry["embedding_mode"] == "HUGGINGFACE_REAL_MODEL"
    assert telemetry["vector_backend"] == "SUPABASE_PGVECTOR"
    assert telemetry["llm_provider"] == "google_ai_studio"

