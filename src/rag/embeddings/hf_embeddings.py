"""
Generador de Embeddings Semánticos con Hugging Face / sentence-transformers.
Modelo predeterminado: sentence-transformers/all-MiniLM-L6-v2 (384 dimensiones).
"""
from typing import List
import os
import httpx


class HuggingFaceEmbeddingsGenerator:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", api_token: str = None):
        self.model_name = model_name
        self.api_token = api_token or os.getenv("HF_TOKEN", "")
        self.api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{self.model_name}"
        self.dimension = 384

    def embed_query(self, text: str) -> List[float]:
        """Genera embedding para una consulta de búsqueda."""
        embeddings = self.embed_documents([text])
        return embeddings[0] if embeddings else [0.0] * self.dimension

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para un lote de documentos clínicos."""
        if not self.api_token:
            # Fallback determinístico / mock para entornos CI o sin clave
            return [[0.01 * (i % 10) for i in range(self.dimension)] for _ in texts]

        headers = {"Authorization": f"Bearer {self.api_token}"}
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(self.api_url, headers=headers, json={"inputs": texts, "options": {"wait_for_model": True}})
                if response.status_code == 200:
                    return response.json()
                else:
                    return [[0.01 * (i % 10) for i in range(self.dimension)] for _ in texts]
        except Exception:
            return [[0.01 * (i % 10) for i in range(self.dimension)] for _ in texts]
