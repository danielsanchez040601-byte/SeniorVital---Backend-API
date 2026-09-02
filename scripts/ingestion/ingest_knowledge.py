"""
Script de Ingesta y Vectorización de la Base de Conocimiento Clínico.
Lee data/knowledge_base/clinical_knowledge_base.json, aplica chunking e indexa en Supabase pgvector con telemetría post-ejecución.
"""
import os
import sys
import json
import asyncio

# Permitir ejecución directa desde la raíz del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.knowledge.chunking.chunker import ClinicalSemanticChunker
from src.rag.embeddings.hf_embeddings import HuggingFaceEmbeddingsGenerator
from src.rag.vector_store.pgvector_store import PgVectorStore
from src.database.database import AsyncSessionLocal


async def main():
    print("[SeniorVital] Iniciando pipeline de ingesta clinica...")

    kb_path = os.path.join("data", "knowledge_base", "clinical_knowledge_base.json")
    if not os.path.exists(kb_path):
        print(f"[Error] Archivo de base de conocimiento no encontrado en {kb_path}")
        return

    with open(kb_path, "r", encoding="utf-8") as f:
        kb_data = json.load(f)

    # 1. Chunking semántico
    chunker = ClinicalSemanticChunker(chunk_size=400, chunk_overlap=60)
    chunks = chunker.chunk_pathology_data(kb_data)
    print(f"[Chunking] Chunks generados exitosamente: {len(chunks)} fragmentos clinicos estructurados.")

    # 2. Generación de Embeddings con Telemetría
    embeddings_gen = HuggingFaceEmbeddingsGenerator()
    texts = [c["content"] for c in chunks]
    print(f"[Embeddings] Generando representaciones vectoriales (384d) para {len(texts)} documentos...")
    vectors, emb_mode = embeddings_gen.embed_documents_with_telemetry(texts)
    print(f"[Embeddings] {len(vectors)} vectores (384d) generados | Modo efectivo: [{emb_mode}].")

    # 3. Inicialización y almacenamiento en Base Vectorial con Telemetría
    vector_store = PgVectorStore(table_name="clinical_knowledge_embeddings")
    backend_status = "IN_MEMORY_FALLBACK"
    try:
        async with AsyncSessionLocal() as session:
            await vector_store.init_vector_table(session)
            backend_status = await vector_store.insert_chunks(chunks, vectors, session=session)
            print(f"[VectorStore] Indexación completada en backend: [{backend_status}] (Supabase pgvector).")
    except Exception as e:
        backend_status = await vector_store.insert_chunks(chunks, vectors, session=None)
        print(f"[VectorStore Aviso]: {e}")
        print(f"[VectorStore] Indexación completada en backend: [{backend_status}].")

    print(f"[SUCCESS] Ingesta completada con éxito. [Embeddings: {emb_mode} | Backend: {backend_status}]")


if __name__ == "__main__":
    asyncio.run(main())
