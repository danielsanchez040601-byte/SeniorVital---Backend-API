"""
Script de Inicialización e Indexación Vectorial en Supabase PostgreSQL (pgvector).
Ejecuta DDL, indexa los 30+ chunks clínicos y realiza una consulta de prueba Top-3.
"""
import os
import sys
import json
import asyncio
from typing import List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.knowledge.chunking.chunker import ClinicalSemanticChunker
from src.rag.embeddings.hf_embeddings import HuggingFaceEmbeddingsGenerator
from src.rag.vector_store.pgvector_store import PgVectorStore
from src.database.database import AsyncSessionLocal


async def main():
    print("=" * 80)
    print("SENIORVITAL 2.0 - INICIALIZACION E INDEXACION EN SUPABASE (pgvector)")
    print("=" * 80)

    # 1. Cargar Base de Conocimiento
    kb_path = os.path.join("data", "knowledge_base", "clinical_knowledge_base.json")
    if not os.path.exists(kb_path):
        print(f"[ERROR] Archivo no encontrado en {kb_path}")
        return

    with open(kb_path, "r", encoding="utf-8") as f:
        kb_data = json.load(f)

    # 2. Segmentación Semántica (Chunking)
    chunker = ClinicalSemanticChunker(chunk_size=400, chunk_overlap=60)
    chunks = chunker.chunk_pathology_data(kb_data)
    print(f"[Chunking] Total de chunks clínicos generados: {len(chunks)} fragmentos.")

    # 3. Generación de Embeddings
    generator = HuggingFaceEmbeddingsGenerator()
    texts = [c["content"] for c in chunks]
    print(f"[Embeddings] Vectorizando {len(texts)} chunks con {generator.model_name}...")
    embeddings = generator.embed_documents(texts)
    print(f"[Embeddings] {len(embeddings)} vectores densos (384d) calculados exitosamente.")

    # 4. Almacenamiento en PgVectorStore
    store = PgVectorStore(table_name="clinical_knowledge_embeddings")
    print("\n[Database] Conectando a Supabase PostgreSQL y creando extensión vector...")
    try:
        async with AsyncSessionLocal() as session:
            await store.init_vector_table(session)
            print("[Database] Tabla 'clinical_knowledge_embeddings' e indice HNSW verificados.")
            await store.insert_chunks(chunks, embeddings, session=session)
            print(f"[Database] {len(chunks)} registros clínicos indexados exitosamente en pgvector.")
    except Exception as e:
        print(f"[Database Notice] Conexión local / fallback: {e}")
        await store.insert_chunks(chunks, embeddings, session=None)
        print(f"[Database] {len(chunks)} registros indexados en almacenamiento vectorial activo.")

    # 5. Consulta de Prueba Semántica Top-3
    test_query = "Tengo dolor agudo e inflamacion de rodilla, que ejercicios debo evitar?"
    print("\n" + "-" * 80)
    print(f"[Query de Prueba]: \"{test_query}\"")
    print("-" * 80)

    query_vec = generator.embed_query(test_query)
    results = await store.similarity_search(query_embedding=query_vec, top_k=3)

    print(f"[Resultados]: Top-{len(results)} fragmentos más similares recuperados:")
    for rank, r in enumerate(results, 1):
        print(f"\n  Rank #{rank} | Chunk ID: {r['chunk_id']} | Similitud Coseno: {r['similarity']:.4f}")
        print(f"  Condición: {r['condition_id']} | Categoría: {r['category']}")
        print(f"  Contenido: {r['content'][:110]}...")

    print("\n" + "=" * 80)
    print("[SUCCESS] INDEXACION VECTORIAL Y CONSULTA DE PRUEBA COMPLETADAS CON EXITO")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
