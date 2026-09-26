# 🗄️ Issue S1-04: Base de Datos Vectorial con pgvector (Supabase PostgreSQL)

> **Materia:** Sistemas Inteligentes — Dra. Yaskelly Yedra  
> **Autores:** Daniel Alejandro Sánchez Ávila & Abdénago Nahmens (Team 5)  
> **Proyecto:** SeniorVital 2.0 — Plataforma Inteligente Wellness (+60)  
> **Sprint Técnico:** Sprint 1 — Ingeniería del Conocimiento y Sistemas RAG  

---

## 🎯 1. Arquitectura de Almacenamiento Vectorial
Se integró la extensión **`pgvector`** sobre **Supabase PostgreSQL**, permitiendo almacenar tanto los registros transaccionales como los embeddings en una única base de datos relacional ACID con índice `HNSW`.

---

## 🛠️ 2. Esquema DDL e Indexación HNSW con Telemetría Post-Ejecución

```sql
-- Habilitar extensión vectorial
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabla de vectores de conocimiento clínico
CREATE TABLE IF NOT EXISTS clinical_knowledge_embeddings (
    id SERIAL PRIMARY KEY,
    chunk_id VARCHAR(64) UNIQUE NOT NULL,
    condition_id VARCHAR(32) NOT NULL,
    category VARCHAR(64) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding vector(384)
);

-- Índice HNSW optimizado para similitud de coseno
CREATE INDEX IF NOT EXISTS idx_clinical_knowledge_embeddings_hnsw 
ON clinical_knowledge_embeddings USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### Lógica de Registro de Backend Post-Ejecución (`PgVectorStore`):
```python
try:
    # Intento real contra Supabase PostgreSQL + pgvector
    results = execute_pgvector_query(query_vector, top_k)
    backend_used = "SUPABASE_PGVECTOR"
except Exception as e:
    logger.warning(f"Fallo en conexión/consulta pgvector: {e}")
    results = memory_fallback_search(query_vector, top_k)
    backend_used = "IN_MEMORY_FALLBACK"
```

---

## 🔬 3. Evidencia Empírica de Indexación y Búsqueda (`index_pgvector.py`)

Salida real obtenida en consola al ejecutar `python scripts/indexing/index_pgvector.py`:

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
  Contenido: CONTRAINDICACIONES ESTRICTAS Y FILTROS DUROS PARA Osteoartritis de Rodilla y Cadera:
MOVIMIENTOS Y ACCIONES PROHIBIDAS...

  Rank #2 | Chunk ID: OA-01_REC | Similitud Coseno: 0.7625 | Backend: SUPABASE_PGVECTOR
  Condición: OA-01 | Categoría: recommended_exercises
  Contenido: PRESCRIPCIÓN DE EJERCICIO PARA Osteoartritis de Rodilla y Cadera:
MODALIDADES RECOMENDADAS: Cadena cinética cerrada...

  Rank #3 | Chunk ID: OA-01_DESC | Similitud Coseno: 0.6889 | Backend: SUPABASE_PGVECTOR
  Condición: OA-01 | Categoría: clinical_profile
  Contenido: PATOLOGÍA: Osteoartritis de Rodilla y Cadera (Código: OA-01, Categoría: Musculoesquelética)...

================================================================================
[INDEXING REPORT] Chunks indexados: 30 | Backend efectivo: SUPABASE_PGVECTOR
[SUCCESS] INDEXACION VECTORIAL Y CONSULTA DE PRUEBA COMPLETADAS CON EXITO
================================================================================
```

---

## 🔒 4. Seguridad y DevSecOps
- No se exponen credenciales de base de datos ni tokens en el repositorio.
- Las variables `DATABASE_URL` y secretos se configuran de forma segura en variables de entorno locales y en los entornos de staging/producción (Render / GitHub Secrets).
