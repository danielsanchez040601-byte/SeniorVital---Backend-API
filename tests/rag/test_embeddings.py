import pytest
from src.rag.embeddings.hf_embeddings import HuggingFaceEmbeddingsGenerator

def test_embeddings_generator_returns_384_dimension_vector():
    generator = HuggingFaceEmbeddingsGenerator()
    query = "Ejercicios seguros para osteoartritis de rodilla"
    vec = generator.embed_query(query)

    assert isinstance(vec, list)
    assert len(vec) == 384
