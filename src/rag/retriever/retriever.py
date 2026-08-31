"""
Recuperador Semántico Clínico con Filtrado por Metadatos.
"""
from typing import List, Dict, Any, Optional
from ..embeddings.hf_embeddings import HuggingFaceEmbeddingsGenerator
from ..vector_store.pgvector_store import PgVectorStore
from sqlalchemy.ext.asyncio import AsyncSession


class ClinicalRetriever:
    def __init__(self, embeddings_gen: Optional[HuggingFaceEmbeddingsGenerator] = None, vector_store: Optional[PgVectorStore] = None):
        self.embeddings_gen = embeddings_gen or HuggingFaceEmbeddingsGenerator()
        self.vector_store = vector_store or PgVectorStore()

    async def retrieve(
        self, 
        session: AsyncSession, 
        query: str, 
        top_k: int = 3, 
        pathology_filter: Optional[str] = None,
        min_similarity: float = 0.65
    ) -> List[Dict[str, Any]]:
        """Recupera fragmentos relevantes aplicando umbral de similitud."""
        query_vec = self.embeddings_gen.embed_query(query)
        results = await self.vector_store.similarity_search(
            session=session,
            query_embedding=query_vec,
            top_k=top_k,
            pathology_filter=pathology_filter
        )
        return [r for r in results if r["similarity"] >= min_similarity]
