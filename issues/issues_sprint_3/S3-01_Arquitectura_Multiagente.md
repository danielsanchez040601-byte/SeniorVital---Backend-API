# 🏛️ Issue S3-01: Arquitectura del Ecosistema Multiagente y Orquestación Jerárquica

**Materia:** Sistemas Inteligentes  
**Docente:** Dra. Yaskelly Yedra  
**Autores:** Daniel Alejandro Sánchez Ávila & Abdenago Nahmens  
**Proyecto:** SeniorVital 2.0 — Sistemas Multiagentes y Orquestación  
**Sprint Técnico:** Sprint 3 — Arquitectura Multiagente y Supervisor Pattern  

---

## 🏛️ 1. Diagrama de Orquestación del Ecosistema Multiagente (Mermaid)

```mermaid
graph TB
    subgraph Entrada["1. Petición de Entrada"]
        Senior["Adulto Mayor (+60 años)"]
        Caregiver["Cuidador / Modo Lectura"]
        API["FastAPI Entrypoint (/api/v1/chat /routines/generate)"]
    end

    subgraph Supervisor["2. Capa de Orquestación (Supervisor Pattern)"]
        Orchestrator["SupervisorOrchestrator (multi_agent_orchestrator.py)"]
        RouterPolicy["Clasificador de Intención & Protocolo A2A"]
    end

    subgraph Agentes_Especializados["3. Agentes Especializados de Dominio"]
        Analytics["AnalyticsAgent (Analítica & Fatiga)"]
        Motivation["MotivationAgent (Empatía & Refuerzo)"]
        Coach["WellnessCoachAgent (ReAct & Prescripción)"]
        QA["QAArchitectAgent (Auditoría ISO/IEC 25010)"]
    end

    subgraph Persistencia_Supabase["4. Persistencia Unificada (Supabase PostgreSQL)"]
        Supa_Pooler[("Supabase PgBouncer Pooler (Puerto 6543)")]
        Table_Routines[("daily_routines (SQL/JSONB)")]
        Table_Records[("exercise_records (RPE Borg)")]
        Table_Profiles[("senior_profiles")]
        Table_Knowledge[("clinical_knowledge (pgvector 384d)")]
    end

    subgraph Inferencia["5. Capa de Inferencia LLM Resiliente"]
        Gemini["Google AI Studio (Gemini 3.6 Flash)"]
        OpenRouter["OpenRouter (Fallback Pool Libre)"]
    end

    Senior --> API
    Caregiver --> API
    API --> Orchestrator
    Orchestrator --> RouterPolicy

    RouterPolicy -->|Paso 1: Analítica y Riesgo| Analytics
    RouterPolicy -->|Paso 2: Mensaje Motivacional| Motivation
    RouterPolicy -->|Paso 3: Razonamiento Clínico| Coach
    RouterPolicy -->|Paso 4: Auditoría de Seguridad| QA

    Analytics --> Supa_Pooler
    Coach --> Supa_Pooler
    Coach --> Table_Knowledge
    Supa_Pooler --> Table_Routines
    Supa_Pooler --> Table_Records
    Supa_Pooler --> Table_Profiles

    Coach --> Gemini
    Gemini -.->|Falla 429/503| OpenRouter

    QA -->|Veredicto: APPROVED| Orchestrator
    Orchestrator --> API
    API --> Senior
```

---

## 🎯 2. Justificación del Patrón Supervisor Jerárquico

* **Evita Ciclos Infinitos:** A diferencia de redes conversacionales no estructuradas (*Autogen o Swarm libre*), el Supervisor centraliza el flujo de control de forma acíclica y determinista.
* **Separación de Responsabilidades:** Cada agente atiende una dimensión clínica o técnica específica (analítica, motivación, razonamiento biomecánico o auditoría de calidad).
* **Cumplimiento ISO/IEC 25010:** El agente `QAArchitectAgent` intercepta las respuestas antes de su entrega al usuario para asegurar accesibilidad gerontológica (WCAG 2.1 AA) y ausencia total de prescripciones lesionales.
