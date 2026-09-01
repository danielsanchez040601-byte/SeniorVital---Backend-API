# 🏛️ Arquitectura Consolidada del Sistema RAG — SeniorVital 2.0

> **Materia:** Sistemas Inteligentes — Dra. Yaskelly Yedra  
> **Autores:** Daniel Alejandro Sánchez Ávila & Abdénago Nahmens (Team 5)  
> **Asesoría Clínica:** Ing. Julio Matute  
> **Sprint Técnico:** Sprint 1 — Ingeniería del Conocimiento y Sistemas RAG  

---

## 1. Diagrama Detallado de Interacción de Componentes

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
        LLM_Primary["Google AI Studio (Gemini 1.5 Flash)"]
        LLM_Fallback["OpenRouter Fallback Pool"]
        Deterministic_Engine["Motor Clínico Determinista (Zero-Hallucination)"]
        
        Pipeline --> Prompt
        Prompt --> LLM_Primary
        LLM_Primary -.->|Fallback 429/503| LLM_Fallback
        LLM_Fallback -.->|Fallback Offline| Deterministic_Engine
    end

    subgraph Output_Layer [5. Prescripción Adaptada Segura]
        Response["Plan de Ejercicio Dosificado + Advertencias Médicas"]
        LLM_Primary --> Response
        LLM_Fallback --> Response
        Deterministic_Engine --> Response
    end
```

---

## 2. Responsabilidad de Componentes y Decisiones de Diseño

1. **`src/knowledge/chunking/chunker.py` (`ClinicalSemanticChunker`):**  
   Segmenta el conocimiento en 3 unidades semánticas por condición (`_DESC`, `_REC`, `_CONTRA`), garantizando que las contraindicaciones nunca queden truncadas y preservando los niveles de progresión segura (1-4).
2. **`src/rag/embeddings/hf_embeddings.py` (`HuggingFaceEmbeddingsGenerator`):**  
   Produce vectores unitarios de dimensión 384 usando `sentence-transformers/all-MiniLM-L6-v2`. Incluye discriminación formal entre modo real y fallback determinista para entornos CI/Testing.
3. **`src/rag/vector_store/pgvector_store.py` (`PgVectorStore`):**  
   Gestiona la persistencia en PostgreSQL con índice HNSW (`m=16, ef_construction=64`) en Supabase, permitiendo un stack unificado transaccional y vectorial con $0 FinOps.
4. **`src/rag/retriever/retriever.py` (`ClinicalRetriever`):**  
   Orquesta la vectorización de consultas y la recuperación Top-K aplicando filtros por patología y umbrales mínimos de similitud.
5. **`src/rag/pipeline/rag_pipeline.py` (`ClinicalRAGPipeline`):**  
   Ensambla el prompt con guardrails, realiza el filtrado de consultas fuera de dominio y orquesta la inferencia resiliente con Google AI Studio y OpenRouter.

---

## 3. Matriz de Trazabilidad S1-01 $\rightarrow$ S1-07

| Issue | Componente en `/src` | Documentación en `/docs` | Script / Prueba | Métrica / Resultado |
| :--- | :--- | :--- | :--- | :--- |
| **S1-01** | `data/knowledge_base/` | `docs/knowledge/` | Inspección JSON | 10 condiciones clínicas y asesoría Ing. Julio Matute |
| **S1-02** | `src/knowledge/chunking/` | `docs/rag/chunking-strategy.md` | `tests/rag/test_chunking.py` | 30 chunks con metadatos preservados |
| **S1-03** | `src/rag/embeddings/` | `docs/rag/embeddings-strategy.md` | `scripts/evaluation/test_hf_embeddings.py` | Modelo all-MiniLM-L6-v2 ($d=384$) |
| **S1-04** | `src/rag/vector_store/` | `docs/rag/vector-database.md` | `scripts/indexing/index_pgvector.py` | Índice HNSW en PostgreSQL / pgvector |
| **S1-05** | `src/rag/pipeline/` | `docs/architecture/rag-architecture.md` | `scripts/evaluation/demo_rag_pipeline.py` | Flujo E2E contextualizado con LLM |
| **S1-06** | `data/evaluation/` | `docs/evaluation/retrieval-metrics.md` | `scripts/evaluation/evaluate_rag.py` | Hit Rate@3 = 100%, MRR = 1.0000 |
| **S1-07** | Consolidación | `docs/reports/sprint-1-report.md` | `pytest tests/rag/` | 100% de los tests en verde |
