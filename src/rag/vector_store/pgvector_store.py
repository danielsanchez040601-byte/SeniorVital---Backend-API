"""
Adaptador de Persistencia Vectorial con Supabase PostgreSQL y pgvector.
Soporta inserción masiva, indexación HNSW y búsqueda por similitud de coseno.
"""
from typing import List, Dict, Any, Optional
import json
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class PgVectorStore:
    def __init__(self, table_name: str = "clinical_knowledge_embeddings"):
        self.table_name = table_name
        self._in_memory_records: List[Dict[str, Any]] = []

    async def init_vector_table(self, session: Optional[AsyncSession] = None):
        """Crea la tabla y la extensión pgvector si no existen en Supabase."""
        ddl = f"""
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id SERIAL PRIMARY KEY,
            chunk_id VARCHAR(64) UNIQUE NOT NULL,
            condition_id VARCHAR(32) NOT NULL,
            category VARCHAR(64) NOT NULL,
            content TEXT NOT NULL,
            metadata JSONB DEFAULT '{{}}'::jsonb,
            embedding vector(384)
        );
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_hnsw 
        ON {self.table_name} USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
        """
        if session:
            try:
                await session.execute(text(ddl))
                await session.commit()
            except Exception as e:
                # Si no hay conexión activa, se mantiene la estructura en memoria
                pass

    async def insert_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]], session: Optional[AsyncSession] = None):
        """Inserta chunks y sus correspondientes embeddings."""
        for c, emb in zip(chunks, embeddings):
            record = {
                "chunk_id": c.get("chunk_id", ""),
                "condition_id": c.get("pathology_id", c.get("condition_id", "GEN")),
                "category": c.get("chunk_type", c.get("category", "clinical")),
                "content": c.get("content", ""),
                "metadata": c.get("metadata", {}),
                "embedding": emb
            }
            self._in_memory_records.append(record)

        if session:
            try:
                for r in self._in_memory_records[-len(chunks):]:
                    emb_str = f"[{','.join(map(str, r['embedding']))}]"
                    meta_json = json.dumps(r['metadata'])
                    stmt = text(f"""
                        INSERT INTO {self.table_name} (chunk_id, condition_id, category, content, metadata, embedding)
                        VALUES (:cid, :cond, :cat, :cnt, :meta::jsonb, '{emb_str}'::vector)
                        ON CONFLICT (chunk_id) DO UPDATE 
                        SET content = EXCLUDED.content, metadata = EXCLUDED.metadata, embedding = EXCLUDED.embedding;
                    """)
                    await session.execute(stmt, {
                        "cid": r["chunk_id"],
                        "cond": r["condition_id"],
                        "cat": r["category"],
                        "cnt": r["content"],
                        "meta": meta_json
                    })
                await session.commit()
            except Exception:
                pass

    async def similarity_search(
        self, 
        query_embedding: List[float], 
        top_k: int = 3,
        condition_filter: Optional[str] = None,
        session: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """Realiza búsqueda semántica por similitud de coseno."""
        if session:
            try:
                emb_str = f"[{','.join(map(str, query_embedding))}]"
                where_clause = ""
                params = {"k": top_k}
                if condition_filter:
                    where_clause = "WHERE condition_id = :cond"
                    params["cond"] = condition_filter

                query = text(f"""
                    SELECT chunk_id, condition_id, category, content, metadata,
                           1 - (embedding <=> '{emb_str}'::vector) AS similarity
                    FROM {self.table_name}
                    {where_clause}
                    ORDER BY embedding <=> '{emb_str}'::vector ASC
                    LIMIT :k;
                """)
                res = await session.execute(query, params)
                rows = res.fetchall()
                if rows:
                    return [
                        {
                            "chunk_id": r[0],
                            "condition_id": r[1],
                            "category": r[2],
                            "content": r[3],
                            "metadata": r[4],
                            "similarity": round(float(r[5]), 4) if r[5] is not None else 0.0
                        }
                        for r in rows
                    ]
            except Exception:
                pass

        # Búsqueda semántica sobre registros cargados en memoria
        candidates = self._in_memory_records
        if condition_filter:
            candidates = [r for r in candidates if r["condition_id"] == condition_filter]

        scored = []
        for r in candidates:
            sim = cosine_similarity(query_embedding, r["embedding"])
            scored.append({
                "chunk_id": r["chunk_id"],
                "condition_id": r["condition_id"],
                "category": r["category"],
                "content": r["content"],
                "metadata": r["metadata"],
                "similarity": round(sim, 4)
            })

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:top_k]
