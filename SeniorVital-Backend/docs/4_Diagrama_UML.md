# 📐 Modelado Arquitectónico y Diagramas UML — SeniorVital
**Documentación Viva como Código (*Markdown as-Code con Mermaid.js*)**

---

## 1. Diagrama de Arquitectura de Componentes (C4 Nivel 2)

```mermaid
graph TB
    subgraph Cliente["Capa de Presentación (Frontend Web)"]
        UI_Senior["Módulo Adulto Mayor (Home, RPE, Hábitos)"]
        UI_Caregiver["Módulo Cuidador (Vista Espejo)"]
        UI_Admin["Módulo Fisioterapeuta (Panel Clínico)"]
    end

    subgraph Backend["Capa de Servicios y Negocio (FastAPI en Render)"]
        Router_Auth["Router: /auth (Seguridad & JWT)"]
        Router_Routines["Router: /routines (Prescripción AI)"]
        Router_Exercises["Router: /api/v1/exercises (Catálogo)"]
        Router_Chat["Router: /api/v1/chat (Asistente RAG)"]
        
        Agent_Wellness["Agente Wellness Coach (LangGraph)"]
        Agent_Preventive["Agente Preventivo (Fatiga & Inactividad)"]
        Guardrails["Capa de Seguridad Clínica (Guardrails)"]
    end

    subgraph Persistencia["Capa de Datos y Memoria Vectorial"]
        DB_SQL["PostgreSQL Relacional (Usuarios, Rutinas, RPE)"]
        DB_Vector["Extensión pgvector (Embeddings 384d)"]
    end

    subgraph Inferencia["Proveedores de IA en la Nube"]
        Google_AI["Google AI Studio (Gemini 3.6 Flash)"]
        OpenRouter_Pool["OpenRouter (Fallback Multimodelo)"]
    end

    UI_Senior -->|REST / JSON / JWT| Router_Auth
    UI_Senior -->|REST / JSON| Router_Routines
    UI_Senior -->|REST / JSON| Router_Chat
    UI_Caregiver -->|REST / JSON| Router_Routines
    UI_Admin -->|REST / JSON| Router_Exercises

    Router_Routines --> Agent_Wellness
    Router_Chat --> Agent_Wellness
    Agent_Wellness --> Guardrails
    Agent_Wellness --> DB_Vector
    Agent_Wellness -->|Inferencia Directa| Google_AI
    Agent_Wellness -.->|Conmutación ante 429| OpenRouter_Pool

    Router_Auth --> DB_SQL
    Router_Exercises --> DB_SQL
    Router_Routines --> DB_SQL
    Agent_Preventive --> DB_SQL
```

---

## 2. Diagrama Entidad-Relación (ERD de Base de Datos)

```mermaid
erDiagram
    USERS ||--o| SENIOR_PROFILES : "posee"
    USERS ||--o{ DAILY_ROUTINES : "recibe"
    USERS ||--o{ EXERCISE_RECORDS : "registra"
    USERS ||--o{ HEALTH_EVENTS : "reporta"
    DAILY_ROUTINES ||--|{ ROUTINE_EXERCISES : "contiene"
    EXERCISES ||--o{ ROUTINE_EXERCISES : "referenciado en"

    USERS {
        int id PK
        string email UK
        string password_hash
        string full_name
        string role "senior | caregiver | admin"
        timestamp created_at
    }

    SENIOR_PROFILES {
        int id PK
        int user_id FK
        int age
        float weight_kg
        float height_cm
        string[] medical_conditions
        int fitness_level "1 a 3"
        string[] equipment_available
        string objectives
    }

    EXERCISES {
        int id PK
        string name
        string description
        string video_url
        int progression_level "1 a 4"
        string[] contraindications
        string[] target_muscles
    }

    DAILY_ROUTINES {
        int id PK
        int senior_id FK
        date assigned_date
        string status "PENDING | COMPLETED | SKIPPED"
        jsonb exercises_data
        jsonb warmup_data
    }

    EXERCISE_RECORDS {
        int id PK
        int senior_id FK
        int exercise_id FK
        int sets_completed
        int reps_completed
        int rpe_score "1 a 10"
        string reported_pain "Sin Dolor | Rodilla | Espalda | Hombro | etc"
        timestamp recorded_at
    }

    HEALTH_EVENTS {
        int id PK
        int user_id FK
        string event_type "FATIGUE_ALERT | INACTIVITY | PAIN_SPIKE"
        jsonb details
        timestamp created_at
    }
```

---

## 3. Diagrama de Secuencia: Prescripción Inteligente y Registro RPE

```mermaid
sequenceDiagram
    autonumber
    actor Senior as Adulto Mayor
    participant App as Frontend (Home.jsx)
    participant API as FastAPI Backend (/routines)
    participant Agent as Wellness Coach (LangGraph)
    participant DB as Supabase PostgreSQL
    participant AI as Google AI Studio (Gemini 3.6 Flash)

    Senior->>App: Abre la aplicación
    App->>API: GET /routines/today?user_id=1
    API->>DB: Consultar rutina del día
    alt Rutina ya existe
        DB-->>API: Retorna DailyRoutine
        API-->>App: JSON Rutina (200 OK)
    else No existe rutina
        API->>DB: Obtener perfil médico (Edad: 72, Artrosis)
        DB-->>API: SeniorProfile
        API->>Agent: Invocar generación de rutina
        Agent->>AI: Solicitar prescripción adaptada
        AI-->>Agent: JSON con warmup + 3 ejercicios seguros
        Agent->>DB: INSERT INTO daily_routines
        DB-->>API: Confirmación de persistencia
        API-->>App: JSON Rutina generada (200 OK)
    end
    App-->>Senior: Muestra rutina y videos en pantalla

    Senior->>App: Toca "Registrar Esfuerzo" (RPE=5, Sin Dolor)
    App->>API: POST /tracking/record (RPE=5, pain=None)
    API->>DB: INSERT INTO exercise_records
    DB-->>API: OK
    API-->>App: Registro completado con éxito
    App-->>Senior: Refuerzo positivo y actualización de calendario
```
