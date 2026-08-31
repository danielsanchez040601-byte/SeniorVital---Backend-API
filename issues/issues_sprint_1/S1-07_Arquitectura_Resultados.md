# 🏛️ Issue S1-07: Arquitectura Integral del Sistema RAG y Diagramas Mermaid

**Materia:** Sistemas Inteligentes  
**Docente:** Dra. Yaskelly Yedra  
**Autores:** Daniel Alejandro Sánchez Ávila & Abdenago Nahmens  
**Proyecto:** SeniorVital 2.0 — Sistema RAG Gerontológico  
**Sprint Técnico:** Sprint 1 — Ingeniería del Conocimiento y Sistemas RAG  

---

## 🏛️ 1. Diagrama de Arquitectura de Capas RAG

```mermaid
graph TB
    subgraph Capa_Cliente["1. Capa Cliente & Experiencia de Usuario"]
        UI["SeniorVital Frontend (React 18 + Vite)"]
        ChatUI["Módulo de Chat Conversacional"]
        RoutineUI["Módulo de Prescripción Diaria"]
    end

    subgraph Capa_Servicios["2. Capa de Servicios y Enrutamiento (FastAPI)"]
        API["FastAPI Application Core"]
        RouterChat["/api/v1/chat"]
        RouterRoutine["/routines/generate"]
        RAGProcessor["RAG Processor (rag_processor.py)"]
    end

    subgraph Capa_Embeddings["3. Capa de Vectorización Semántica"]
        HF["Hugging Face (sentence-transformers/all-MiniLM-L6-v2)"]
        Vec_Query["Vector de Consulta (384d Normalizado)"]
    end

    subgraph Capa_Persistencia["4. Capa de Persistencia Vectorial (Supabase)"]
        Supa_Pooler[("Supabase PgBouncer Pooler (Puerto 6543)")]
        Table_Rel[("Tablas Relacionales: users, senior_profiles, routines")]
        Table_Vec[("Tabla Vectorial: clinical_knowledge (pgvector 384d)")]
        Index_IVFFlat["Índice IVFFlat (Cosine Similarity)"]
    end

    subgraph Capa_Seguridad_Inferencia["5. Capa de Seguridad & Modelos LLM"]
        Guardrails["Guardrails de Seguridad Clínica & Filtros Duros"]
        Gemini["Google AI Studio (Gemini 3.6 Flash - Modelo Principal)"]
        OpenRouter["OpenRouter (Fallback Multimodelo Libre)"]
        Deterministic["Generador Clínico Determinístico Local"]
    end

    UI --> API
    API --> RouterChat
    API --> RouterRoutine
    RouterChat --> RAGProcessor
    RouterRoutine --> RAGProcessor

    RAGProcessor --> HF
    HF --> Vec_Query
    Vec_Query --> Supa_Pooler
    Supa_Pooler --> Table_Vec
    Table_Vec --> Index_IVFFlat
    Table_Vec -->|Top-k Chunks| RAGProcessor

    RAGProcessor --> Guardrails
    Guardrails -->|Prompt Aumentado| Gemini
    Gemini -.->|Falla 429 / 503| OpenRouter
    OpenRouter -.->|Falla de Red| Deterministic
    
    Gemini --> RAGProcessor
    OpenRouter --> RAGProcessor
    Deterministic --> RAGProcessor
    RAGProcessor --> API
    API --> UI
```

---

## 🔄 2. Diagrama de Flujo de Datos para Ingesta y Recuperación

```mermaid
flowchart TD
    subgraph Ingesta["Fase de Ingesta y Vectorización"]
        DocClinico["Informe Clínico Maestro (10 Patologías)"] --> Chunking["Segmentación Semántica (40 Chunks Lógicos)"]
        Chunking --> AddMeta["Inyección de Metadatos (Autoría, Fuentes, Reconocimiento Ing. Julio Matute)"]
        AddMeta --> HF_Ingest["Vectorización con Hugging Face (all-MiniLM-L6-v2)"]
        HF_Ingest --> PG_Insert["Persistencia en Supabase clinical_knowledge (pgvector)"]
    end

    subgraph Recuperacion["Fase de Inferencia en Tiempo Real"]
        QueryUser["Consulta del Adulto Mayor"] --> HF_Query["Vectorización de Consulta (384d)"]
        HF_Query --> CosineMatch["Búsqueda por Similitud de Coseno en pgvector"]
        PG_Insert -.-> CosineMatch
        CosineMatch --> TopChunks["Recuperación de Top 3 Chunks Clínicos"]
        TopChunks --> PromptGen["Construcción de Prompt Aumentado + Guardrails"]
        PromptGen --> LLM_Inference["Inferencia con Gemini 3.6 Flash / OpenRouter"]
        LLM_Inference --> RespSafe["Respuesta Segura, Empática y Adaptada al Adulto Mayor"]
    end
```

---

## 🌟 3. Reconocimiento y Créditos del Sprint 1

> **Reconocimiento especial al Ing. Julio Matute por su asesoría técnica y clínica en la validación de patologías, afecciones y enfermedades limitantes en adultos mayores, las cuales fundamentan esta base de conocimiento.**

* **Desarrolladores:** Daniel Alejandro Sánchez Ávila & Abdenago Nahmens.
* **Docente Titular:** Dra. Yaskelly Yedra.
* **Cátedra:** Sistemas Inteligentes — 2026.
