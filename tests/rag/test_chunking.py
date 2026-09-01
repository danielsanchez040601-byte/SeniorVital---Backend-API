import pytest
from src.knowledge.chunking.chunker import ClinicalSemanticChunker

def test_semantic_chunker_generates_three_chunks_per_pathology():
    sample_kb = {
        "pathologies": [
            {
                "id": "TEST-01",
                "name": "Condicion de Prueba",
                "category": "Prueba",
                "description": "Descripcion de prueba.",
                "biomechanical_limitations": ["Limitacion 1"],
                "recommended_modalities": ["Modalidad 1"],
                "strict_contraindications": ["Prohibido saltos"],
                "safe_progression_levels": [1, 2]
            }
        ]
    }
    chunker = ClinicalSemanticChunker()
    chunks = chunker.chunk_pathology_data(sample_kb)

    assert len(chunks) == 3
    assert chunks[0]["chunk_id"] == "TEST-01_DESC"
    assert chunks[1]["chunk_id"] == "TEST-01_REC"
    assert chunks[2]["chunk_id"] == "TEST-01_CONTRA"
    assert "Prohibido saltos" in chunks[2]["content"]
