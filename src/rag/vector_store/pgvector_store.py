"""
Adaptador de Persistencia Vectorial con Supabase PostgreSQL y pgvector.
"""
from typing import List, Dict, Any, Optional
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


class PgVectorStore:
    def __init__(self, table_name: str = "clinical_knowledge_vectors"):
        self.table_name = table_name

    async def init_vector_table(self, session: AsyncSession):
        """Crea la tabla y la extensión pgvector si no existen."""
        ddl = f"""
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id SERIAL PRIMARY KEY,
            chunk_id VARCHAR(64) UNIQUE NOT NULL,
            pathology_id VARCHAR(32) NOT NULL,
            pathology_name VARCHAR(128) NOT NULL,
            chunk_type VARCHAR(64) NOT NULL,
            content TEXT NOT NULL,
            metadata JSONB DEFAULT '{{}}'::jsonb,
            embedding vector(384)
        );
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_embedding 
        ON {self.table_name} USING hnsw (embedding vector_cosine_ops);
        """
        await session.execute(text(ddl))
        await session.commit()

    async def similarity_search(
        self, 
        session: AsyncSession, 
        query_embedding: List[float], 
        top_k: int = 3,
        pathology_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Realiza búsqueda semántica por similitud de coseno."""
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        where_clause = ""
        params = {"k": top_k}
        if pathology_filter:
            where_clause = "WHERE pathology_id = :p_filter"
            params["p_filter"] = pathology_filter

        query = text(f"""
            SELECT chunk_id, pathology_id, pathology_name, chunk_type, content, metadata,
                   1 - (embedding <=> '{embedding_str}'::vector) AS similarity
            FROM {self.table_name}
            {where_clause}
            ORDER BY embedding <=> '{embedding_str}'::vector ASC
            LIMIT :k;
        """)

        result = await session.execute(query, params)
        rows = result.fetchall()
        return [
            {
                "chunk_id": r[0],
                "pathology_id": r[1],
                "pathology_name": r[2],
                "chunk_type": r[3],
                "content": r[4],
                "metadata": r[5],
                "similarity": float(r[6]) if r[6] is not None else 0.0
            }
            for r in rows
        ]
