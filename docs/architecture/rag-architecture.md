# 🏛️ Arquitectura Consolidada del Sistema RAG — SeniorVital 2.0

> **Materia:** Sistemas Inteligentes — Dra. Yaskelly Yedra  
> **Autores:** Daniel Alejandro Sánchez Ávila & Abdénago Nahmens (Team 5)  
> **Asesoría Clínica:** Ing. Julio Matute  
> **Sprint Técnico:** Sprint 1 — Ingeniería del Conocimiento y Sistemas RAG  

---

## 1. Diagrama Detallado de Interacción de Componentes y Telemetría

```mermaid
flowchart TD
    subgraph Knowledge_Engineering [1. Ingesta y Segmentación Semántica]
        Doc["Corpus Clínico (data/knowledge_base/clinical_knowledge_base.json)"]
        Chunker["ClinicalSemanticChunker (src/knowledge/chunking/chunker.py)"]
        HF_Embed["HuggingFaceEmbeddingsGenerator (src/rag/embeddings/hf_embeddings.py)"]
        
        Doc --> Chunker
        Chunker -->|Chunks Tripartitos _DESC, _REC, _CONTRA| HF_Embed
    end

    subgraph Storage_Layer [2. Almacenamiento e Indexación Vectorial]
        PGV[("Supabase PostgreSQL + pgvector (src/rag/vector_store/pgvector_store.py)")]
        HF_Embed -->|Vectores Densos 384d (Norma L2 = 1.0)| PGV
    end

    subgraph Runtime_Retrieval [3. Recuperación Semántica y Guardrails]
        Query["Consulta del Paciente / Perfil Geriátrico"]
        Retriever["ClinicalRetriever (src/rag/retriever/retriever.py)"]
        Pipeline["ClinicalRAGPipeline (src/rag/pipeline/rag_pipeline.py)"]
        
        Query --> Retriever
        PGV <-->|Búsqueda Coseno Top-K=3| Retriever
        Retriever --> Pipeline
    end

    subgraph LLM_Reasoning [4. Inferencia Aumentada y Tolerancia a Fallos]
        Prompt["System Prompt con Contexto Inyectado"]
        LLM_Primary["Google AI Studio (Gemini Flash Lite)"]
        LLM_Fallback["OpenRouter Fallback Pool"]
        Deterministic_Engine["Motor Clínico Determinista (Zero-Hallucination)"]
        
        Pipeline --> Prompt
        Prompt --> LLM_Primary
        LLM_Primary -.->|Fallback 429/503| LLM_Fallback
        LLM_Fallback -.->|Fallback Offline| Deterministic_Engine
    end

    subgraph Output_Layer [5. Prescripción Adaptada y Telemetría Post-Ejecución]
        Response["Respuesta Condicionada + Metadata de Telemetría"]
        LLM_Primary --> Response
        LLM_Fallback --> Response
        Deterministic_Engine --> Response
    end
```

---

## 2. Telemetría en Tiempo de Ejecución (Post-Execution Telemetry)

Para garantizar trazabilidad real y evitar reportes basados en configuración estática, el sistema recopila los backends que **efectivamente produjeron el resultado**:

```json
{
  "query": "Tengo osteoartritis severa en rodilla, ¿puedo hacer sentadillas con salto?",
  "status": "SUCCESS",
  "provider": "Google AI Studio (Gemini Flash Lite) | OpenRouter Fallback Pool",
  "telemetry": {
    "embedding_mode": "HUGGINGFACE_REAL_MODEL | FALLBACK_CI | FALLBACK_API_ERROR",
    "vector_backend": "SUPABASE_PGVECTOR | IN_MEMORY_FALLBACK",
    "llm_provider": "google_ai_studio | openrouter | deterministic_fallback"
  },
  "retrieved_chunks": [ ... ],
  "context_injected": "...",
  "response": "..."
}
```

---

## 3. Responsabilidad de Componentes y Decisiones de Diseño

| Componente | Módulo en `/src` | Responsabilidad Técnica | Decisión de Diseño Justificada |
| :--- | :--- | :--- | :--- |
| **Corpus Clínico** | `data/knowledge_base/` | 10 condiciones clínicas geriátricas estructuradas en JSON. | Validación clínica con el **Ing. Julio Matute**. |
| **Chunker** | `src/knowledge/chunking/` | Divide cada patología en fragmentos (`_DESC`, `_REC`, `_CONTRA`). | Evita contaminación entre prescripciones y contraindicaciones. |
| **Embeddings** | `src/rag/embeddings/` | Genera vectores de 384 dimensiones (`all-MiniLM-L6-v2`). | Telemetría post-ejecución (`HUGGINGFACE_REAL_MODEL` vs fallback). |
| **Vector Store** | `src/rag/vector_store/` | Persistencia en PostgreSQL + `pgvector` con índice `HNSW`. | Registro de backend (`SUPABASE_PGVECTOR` vs `IN_MEMORY_FALLBACK`). |
| **Retriever** | `src/rag/retriever/` | Recuperación semántica Top-K con filtrado por metadatos. | Búsqueda coseno de alta velocidad ($< 5\text{ ms}$). |
| **Pipeline E2E** | `src/rag/pipeline/` | Enrutamiento, guardrails de seguridad y generación LLM. | Guardrail para consultas fuera de dominio (Zero-Context Fallback). |

---

## 4. Matriz de Trazabilidad S1-01 $\rightarrow$ S1-07

| Issue | Entregable en `/src` | Documentación | Script de Prueba | Métrica / Resultado | Estado |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **S1-01** | `data/knowledge_base/` | `docs/knowledge/` | Inspección JSON | 10 condiciones clínicas modeladas | ✅ **100%** |
| **S1-02** | `src/knowledge/chunking/` | `docs/rag/chunking-strategy.md` | `tests/rag/test_chunking.py` | 30 chunks con metadatos | ✅ **100%** |
| **S1-03** | `src/rag/embeddings/` | `docs/rag/embeddings-strategy.md` | `scripts/evaluation/test_hf_embeddings.py` | Modelo 384d, Norma L2 = 1.0000 | ✅ **100%** |
| **S1-04** | `src/rag/vector_store/` | `docs/rag/vector-database.md` | `scripts/indexing/index_pgvector.py` | Índice HNSW en PostgreSQL / pgvector | ✅ **100%** |
| **S1-05** | `src/rag/pipeline/` | `docs/architecture/rag-architecture.md` | `scripts/evaluation/demo_rag_pipeline.py` | Flujo E2E contextualizado con telemetría | ✅ **100%** |
| **S1-06** | `data/evaluation/` | `docs/evaluation/retrieval-metrics.md` | `scripts/evaluation/evaluate_rag.py` | Hit Rate@3 = 100%, MRR = 1.0000 | ✅ **100%** |
| **S1-07** | Consolidación | `docs/reports/sprint-1-report.md` | `pytest tests/rag/ -v` | 100% de la suite en verde | ✅ **100%** |
