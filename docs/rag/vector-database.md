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
* Registrar telemetría post-ejecución (`SUPABASE_PGVECTOR` vs `IN_MEMORY_FALLBACK`).

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

## 🔬 4. Ejecución del Script de Indexación y Telemetría

Para verificar la creación de esquemas y la inserción de chunks:
```bash
python scripts/indexing/index_pgvector.py
```

### Salida de Ejecución:
```text
================================================================================
SENIORVITAL 2.0 - INICIALIZACION E INDEXACION EN SUPABASE (pgvector)
================================================================================
[Chunking] Total de chunks clínicos generados: 30 fragmentos.
[Embeddings] Vectorizando 30 chunks con sentence-transformers/all-MiniLM-L6-v2...
[Embeddings] 30 vectores densos (384d) generados | Modo: [HUGGINGFACE_REAL_MODEL].

[Database] Conectando a Supabase PostgreSQL y creando extensión vector...
[Database] Tabla 'clinical_knowledge_embeddings' e indice HNSW verificados.
[Database] 30 registros clínicos indexados en PostgreSQL/pgvector.

--------------------------------------------------------------------------------
[Query de Prueba]: "Tengo dolor agudo e inflamacion de rodilla, que ejercicios debo evitar?"
--------------------------------------------------------------------------------
[Resultados]: Top-3 fragmentos más similares recuperados:

  Rank #1 | Chunk ID: OA-01_CONTRA | Similitud Coseno: 0.8125 | Backend: SUPABASE_PGVECTOR
  Condición: OA-01 | Categoría: contraindications
  Contenido: CONTRAINDICACIONES ESTRICTAS Y FILTROS DUROS PARA Osteoartritis de Rodilla y Cadera...

  Rank #2 | Chunk ID: OA-01_REC | Similitud Coseno: 0.7625 | Backend: SUPABASE_PGVECTOR
  Condición: OA-01 | Categoría: recommended_exercises
  Contenido: PRESCRIPCIÓN DE EJERCICIO PARA Osteoartritis de Rodilla y Cadera...

  Rank #3 | Chunk ID: OA-01_DESC | Similitud Coseno: 0.6889 | Backend: SUPABASE_PGVECTOR
  Condición: OA-01 | Categoría: clinical_profile
  Contenido: PATOLOGÍA: Osteoartritis de Rodilla y Cadera (Código: OA-01, Categoría: Musculoesquelética)...

================================================================================
[INDEXING REPORT] Chunks indexados: 30 | Backend efectivo: SUPABASE_PGVECTOR
[SUCCESS] INDEXACION VECTORIAL Y CONSULTA DE PRUEBA COMPLETADAS CON EXITO
================================================================================
```
