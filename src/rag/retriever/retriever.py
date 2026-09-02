"""
Recuperador Semántico Clínico con Filtrado por Metadatos y Telemetría Post-Ejecución.
Integra generación de embeddings, consulta a base vectorial y auto-ingesta bajo demanda.
"""
from typing import List, Dict, Any, Optional, Tuple
import os
import json
from sqlalchemy.ext.asyncio import AsyncSession

from ..embeddings.hf_embeddings import HuggingFaceEmbeddingsGenerator
from ..vector_store.pgvector_store import PgVectorStore
from ...knowledge.chunking.chunker import ClinicalSemanticChunker


class ClinicalRetriever:
    def __init__(
        self, 
        embeddings_gen: Optional[HuggingFaceEmbeddingsGenerator] = None, 
        vector_store: Optional[PgVectorStore] = None
    ):
        self.embeddings_gen = embeddings_gen or HuggingFaceEmbeddingsGenerator()
        self.vector_store = vector_store or PgVectorStore()
        self._ensure_knowledge_loaded()

    def _ensure_knowledge_loaded(self):
        """Si el almacén vectorial está vacío en memoria, carga la base de conocimiento clínico."""
        if not self.vector_store._in_memory_records:
            kb_path = os.path.join("data", "knowledge_base", "clinical_knowledge_base.json")
            if os.path.exists(kb_path):
                try:
                    with open(kb_path, "r", encoding="utf-8") as f:
                        kb_data = json.load(f)
                    chunker = ClinicalSemanticChunker(chunk_size=400, chunk_overlap=60)
                    chunks = chunker.chunk_pathology_data(kb_data)
                    texts = [c["content"] for c in chunks]
                    embeddings = self.embeddings_gen.embed_documents(texts)
                    for c, emb in zip(chunks, embeddings):
                        self.vector_store._in_memory_records.append({
                            "chunk_id": c.get("chunk_id", ""),
                            "condition_id": c.get("pathology_id", c.get("condition_id", "GEN")),
                            "category": c.get("chunk_type", c.get("category", "clinical")),
                            "content": c.get("content", ""),
                            "metadata": c.get("metadata", {}),
                            "embedding": emb
                        })
                except Exception:
                    pass

    async def retrieve(
        self, 
        query: str, 
        top_k: int = 3, 
        condition_filter: Optional[str] = None,
        min_similarity: float = 0.0,
        session: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """Recupera fragmentos relevantes aplicando umbral de similitud."""
        query_vec, mode = self.embeddings_gen.embed_query_with_telemetry(query)
        results = await self.vector_store.similarity_search(
            query_embedding=query_vec,
            top_k=top_k,
            condition_filter=condition_filter,
            session=session
        )
        return [r for r in results if r["similarity"] >= min_similarity]

    async def retrieve_with_telemetry(
        self, 
        query: str, 
        top_k: int = 3, 
        condition_filter: Optional[str] = None,
        min_similarity: float = 0.0,
        session: Optional[AsyncSession] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """Recupera fragmentos relevantes y retorna además la telemetría post-ejecución."""
        query_vec, embedding_mode = self.embeddings_gen.embed_query_with_telemetry(query)
        results = await self.vector_store.similarity_search(
            query_embedding=query_vec,
            top_k=top_k,
            condition_filter=condition_filter,
            session=session
        )
        filtered = [r for r in results if r["similarity"] >= min_similarity]
        telemetry = {
            "embedding_mode": embedding_mode,
            "vector_backend": self.vector_store.last_backend_used
        }
        return filtered, telemetry
