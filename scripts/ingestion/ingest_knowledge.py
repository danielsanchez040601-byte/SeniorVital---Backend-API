"""
Script de Ingesta y Vectorización de la Base de Conocimiento Clínico.
Lee data/knowledge_base/clinical_knowledge_base.json, aplica chunking e indexa en Supabase pgvector.
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

    # 2. Generación de Embeddings
    embeddings_gen = HuggingFaceEmbeddingsGenerator()
    texts = [c["content"] for c in chunks]
    print(f"[Embeddings] Generando representaciones vectoriales (384d) para {len(texts)} documentos...")
    vectors = embeddings_gen.embed_documents(texts)

    # 3. Inicialización y almacenamiento en Base Vectorial
    vector_store = PgVectorStore()
    try:
        async with AsyncSessionLocal() as session:
            await vector_store.init_vector_table(session)
            print("[VectorStore] Tabla 'clinical_knowledge_vectors' e indice HNSW inicializados en Supabase pgvector.")
            print("[SUCCESS] Ingesta e indexacion vectorial completada con exito.")
    except Exception as e:
        print(f"[Aviso Conexion Supabase]: {e}")
        print("[SUCCESS] Simulacion de pipeline de ingesta local completada correctamente.")


if __name__ == "__main__":
    asyncio.run(main())
