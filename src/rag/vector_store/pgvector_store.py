"""
Adaptador de Persistencia Vectorial con Supabase PostgreSQL y pgvector.
Soporta inserción masiva, indexación HNSW, búsqueda por similitud de coseno y Telemetría Post-Ejecución.
"""
from typing import List, Dict, Any, Optional
import json
import math
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)


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
        self.last_backend_used = "IN_MEMORY_FALLBACK"

    async def init_vector_table(self, session: Optional[AsyncSession] = None) -> str:
        """Crea la tabla y la extensión pgvector si no existen en Supabase ejecutando comandos atómicos."""
        if session:
            try:
                # Comandos DDL atómicos compatibles con asyncpg
                await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                await session.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        id SERIAL PRIMARY KEY,
                        chunk_id VARCHAR(64) UNIQUE NOT NULL,
                        condition_id VARCHAR(32) NOT NULL,
                        category VARCHAR(64) NOT NULL,
                        content TEXT NOT NULL,
                        metadata JSONB DEFAULT '{{}}'::jsonb,
                        embedding vector(384)
                    );
                """))
                await session.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.table_name}_hnsw 
                    ON {self.table_name} USING hnsw (embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64);
                """))
                await session.commit()
                self.last_backend_used = "SUPABASE_PGVECTOR"
                return "SUPABASE_PGVECTOR"
            except Exception as e:
                logger.warning(f"Fallo en inicialización de tabla pgvector: {e}")
                self.last_backend_used = "IN_MEMORY_FALLBACK"
                return "IN_MEMORY_FALLBACK"
        return "IN_MEMORY_FALLBACK"

    async def insert_chunks(
        self, 
        chunks: List[Dict[str, Any]], 
        embeddings: List[List[float]], 
        session: Optional[AsyncSession] = None
    ) -> str:
        """Inserta chunks y sus correspondientes embeddings registrando el backend efectivo."""
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
                        VALUES (:cid, :cond, :cat, :cnt, CAST(:meta AS jsonb), CAST(:emb AS vector))
                        ON CONFLICT (chunk_id) DO UPDATE 
                        SET content = EXCLUDED.content, metadata = EXCLUDED.metadata, embedding = EXCLUDED.embedding;
                    """)
                    await session.execute(stmt, {
                        "cid": r["chunk_id"],
                        "cond": r["condition_id"],
                        "cat": r["category"],
                        "cnt": r["content"],
                        "meta": meta_json,
                        "emb": emb_str
                    })
                await session.commit()
                self.last_backend_used = "SUPABASE_PGVECTOR"
                return "SUPABASE_PGVECTOR"
            except Exception as e:
                logger.warning(f"Fallo en inserción pgvector: {e}")
                self.last_backend_used = "IN_MEMORY_FALLBACK"
                return "IN_MEMORY_FALLBACK"
        
        self.last_backend_used = "IN_MEMORY_FALLBACK"
        return "IN_MEMORY_FALLBACK"

    async def similarity_search(
        self, 
        query_embedding: List[float], 
        top_k: int = 3,
        condition_filter: Optional[str] = None,
        session: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """Realiza búsqueda semántica por similitud de coseno con telemetría post-ejecución."""
        if session:
            try:
                emb_str = f"[{','.join(map(str, query_embedding))}]"
                where_clause = ""
                params = {"k": top_k, "emb": emb_str}
                if condition_filter:
                    where_clause = "WHERE condition_id = :cond"
                    params["cond"] = condition_filter

                query = text(f"""
                    SELECT chunk_id, condition_id, category, content, metadata,
                           1 - (embedding <=> CAST(:emb AS vector)) AS similarity
                    FROM {self.table_name}
                    {where_clause}
                    ORDER BY embedding <=> CAST(:emb AS vector) ASC
                    LIMIT :k;
                """)
                res = await session.execute(query, params)
                rows = res.fetchall()
                if rows:
                    self.last_backend_used = "SUPABASE_PGVECTOR"
                    return [
                        {
                            "chunk_id": r[0],
                            "condition_id": r[1],
                            "category": r[2],
                            "content": r[3],
                            "metadata": r[4],
                            "similarity": round(float(r[5]), 4) if r[5] is not None else 0.0,
                            "backend_used": "SUPABASE_PGVECTOR"
                        }
                        for r in rows
                    ]
            except Exception as e:
                logger.warning(f"Fallo en consulta pgvector: {e}")

        # Búsqueda semántica sobre registros cargados en memoria
        self.last_backend_used = "IN_MEMORY_FALLBACK"
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
                "similarity": round(sim, 4),
                "backend_used": "IN_MEMORY_FALLBACK"
            })

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:top_k]
