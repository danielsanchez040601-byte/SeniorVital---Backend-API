# 🗄️ Persistencia Vectorial con Supabase PostgreSQL y pgvector

> **Materia:** Sistemas Inteligentes — Dra. Yaskelly Yedra  
> **Autores:** Daniel Sánchez & Abdenago Nahmens | **Asesoría Clínica:** Ing. Julio Matute  

---

## 1. Esquema DDL en PostgreSQL
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS clinical_knowledge_vectors (
    id SERIAL PRIMARY KEY,
    chunk_id VARCHAR(64) UNIQUE NOT NULL,
    pathology_id VARCHAR(32) NOT NULL,
    pathology_name VARCHAR(128) NOT NULL,
    chunk_type VARCHAR(64) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding vector(384)
);

CREATE INDEX IF NOT EXISTS idx_clinical_vectors_hnsw 
ON clinical_knowledge_vectors USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```
