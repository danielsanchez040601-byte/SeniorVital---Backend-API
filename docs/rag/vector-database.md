# 🗄️ Base de Datos Vectorial: PostgreSQL + pgvector en Supabase

> **Materia:** Sistemas Inteligentes — Dra. Yaskelly Yedra  
> **Autores:** Daniel Sánchez & Abdénago Nahmens (Team 5) | **Asesoría Clínica:** Ing. Julio Matute  
> **Script de Inicialización e Indexación:** `scripts/indexing/index_pgvector.py`  

---

## 🏛️ 1. Arquitectura de Almacenamiento Vectorial

En lugar de utilizar bases vectoriales volátiles en memoria o entornos propietarios de pago, **SeniorVital 2.0** utiliza la extensión **`pgvector`** sobre **PostgreSQL 15 (Supabase Cloud)**. Esto permite:
* Persistir registros clínicos transaccionales y representaciones vectoriales en la misma base de datos relacional.
* Mantener consistencia ACID y relaciones por clave foránea entre usuarios, patologías y fragmentos vectoriales.
* Acelerar búsquedas por similitud mediante índices **HNSW (Hierarchical Navigable Small World)**.

---

## 🛠️ 2. Esquema DDL

```sql
-- 1. Habilitar extensión vectorial
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Tabla de embeddings clínicos
CREATE TABLE IF NOT EXISTS clinical_knowledge_embeddings (
    id SERIAL PRIMARY KEY,
    chunk_id VARCHAR(64) UNIQUE NOT NULL,
    condition_id VARCHAR(32) NOT NULL,
    category VARCHAR(64) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding vector(384)
);

-- 3. Índice HNSW optimizado para distancia de coseno
CREATE INDEX IF NOT EXISTS idx_clinical_knowledge_embeddings_hnsw 
ON clinical_knowledge_embeddings USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

---

## 🔍 3. Consulta SQL de Búsqueda Semántica
```sql
SELECT 
    chunk_id, 
    condition_id, 
    category, 
    content, 
    metadata,
    1 - (embedding <=> :query_embedding) AS similarity
FROM clinical_knowledge_embeddings
WHERE 1 - (embedding <=> :query_embedding) >= 0.40
ORDER BY embedding <=> :query_embedding ASC
LIMIT 3;
```

---

## 🔬 4. Ejecución del Script de Indexación
Para inicializar e indexar los 30 fragmentos clínicos estructurados:
```bash
python scripts/indexing/index_pgvector.py
```
Salida confirmada: `30 registros clínicos indexados exitosamente en pgvector con índice HNSW.`
