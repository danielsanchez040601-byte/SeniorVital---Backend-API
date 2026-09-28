# 📐 Sprint 1, 2 & 4: Modelado Visual y Diagramas UML Completos

**Materia:** Ingeniería de Software y Base de Datos  
**Docente:** Dra. Yaskelly Yedra  
**Autores:** Daniel Alejandro Sánchez Ávila & Abdenago Nahmens  
**Proyecto:** SeniorVital — Arquitectura y Modelado Orientado a Objetos  

---

## 👥 1. Diagrama de Casos de Uso del Sistema (UML Use Case Diagram)

```mermaid
graph LR
    Senior((Adulto Mayor))
    Caregiver((Cuidador / Familiar))
    Physio((Fisioterapeuta / Admin))
    LLM((Google Gemini / OpenRouter))

    subgraph SeniorVital_System [Plataforma SeniorVital]
        UC1(CU-01: Iniciar Sesión / Autenticarse)
        UC2(CU-02: Consultar Rutina Diaria)
        UC3(CU-03: Generar Rutina Adaptada con IA)
        UC4(CU-04: Registrar Esfuerzo RPE Borg y Dolor)
        UC5(CU-05: Conversar con Wellness Coach)
        UC6(CU-06: Registrar Hábitos de Agua y Sueño)
        UC7(CU-07: Monitorear Semáforo de Residentes)
        UC8(CU-08: Despachar Alerta SOS / Notificación)
    end

    Senior --> UC1
    Senior --> UC2
    Senior --> UC3
    Senior --> UC4
    Senior --> UC5
    Senior --> UC6
    Senior --> UC8

    Caregiver --> UC1
    Caregiver --> UC7
    Caregiver --> UC8

    Physio --> UC1
    Physio --> UC7

    UC3 -.->|<<include>>| LLM
    UC5 -.->|<<include>>| LLM
```

---

## 🏛️ 2. Diagrama de Clases del Dominio (UML Class Diagram)

```mermaid
classDiagram
    class User {
        +int id
        +string email
        +string password_hash
        +string full_name
        +RoleEnum role
        +datetime created_at
        +verify_password(plain_password) bool
    }

    class RoleEnum {
        <<enumeration>>
        SENIOR
        CAREGIVER
        ADMIN
        PHYSIO
    }

    class SeniorProfile {
        +int id
        +int user_id
        +int fitness_level
        +string mobility_limitations
        +string chronic_conditions
        +string emergency_contact
        +datetime updated_at
    }

    class Exercise {
        +int id
        +string name
        +string description
        +string category
        +int target_rpe
        +string video_url
        +list[float] embedding
    }

    class DailyRoutine {
        +int id
        +int user_id
        +date routine_date
        +string status
        +int perceived_difficulty
        +string ai_feedback
    }

    class ExerciseRecord {
        +int id
        +int user_id
        +int exercise_id
        +int sets_completed
        +int reps_completed
        +int rpe_score
        +string reported_pain
        +datetime recorded_at
    }

    class DailyHabit {
        +int id
        +int user_id
        +date record_date
        +int water_glasses
        +float sleep_hours
    }

    User "1" -- "1" SeniorProfile : posee
    User "1" -- "*" DailyRoutine : tiene asignadas
    User "1" -- "*" ExerciseRecord : registra
    User "1" -- "*" DailyHabit : reporta
    DailyRoutine "*" -- "*" Exercise : contiene
    Exercise "1" -- "*" ExerciseRecord : es ejecutado en
    User --> RoleEnum : clasificado por
```

---

## 🔄 3. Diagrama de Secuencia: Registro de Esfuerzo RPE y Alerta Preventiva

```mermaid
sequenceDiagram
    autonumber
    actor Senior as Adulto Mayor
    participant UI as Frontend React (Modal RPE)
    participant API as FastAPI Router (/tracking/record)
    participant Prev as Agente Preventivo
    participant DB as Supabase PostgreSQL
    participant Push as Servicio Web Push (/notify/send)
    actor Care as Cuidador Asignado

    Senior->>UI: Completa ejercicio y selecciona RPE = 8 ("Muy Difícil") + Dolor Rodilla
    UI->>API: POST /tracking/record (user_id, exercise_id, rpe=8, pain="rodilla")
    API->>DB: INSERT into exercise_records (...)
    DB-->>API: Confirmación de inserción (ID=102)

    API->>Prev: analyze_session_fatigue(user_id, rpe=8, pain="rodilla")
    Prev->>Prev: Evalúa umbrales clínicos (RPE >= 8 -> Alerta Ámbar/Roja)
    
    Prev->>DB: UPDATE senior_status SET risk_level = 'amber'
    Prev->>Push: Trigger notificación de supervisión requerida
    Push-->>Care: Notificación Push: "Carlos reportó fatiga RPE 8 en rodilla"

    API-->>UI: HTTP 200 OK {"status": "success", "alert_triggered": true}
    UI-->>Senior: Muestra mensaje empático de descanso preventivo
```

---

## 🤖 4. Diagrama de Arquitectura del Ecosistema Multi-Agente

```mermaid
flowchart TB
    subgraph Entrada [Capa de Consulta e Interaccion]
        Req["Peticion de Usuario (Rutina o Chat)"]
    end

    subgraph Orquestacion [Orquestador de Agentes]
        Guard["Guardrails Clinicos (Filtro de Emergencias)"]
        Coach["Wellness Coach (Razonamiento Gerontologico)"]
        Prev["Agente Preventivo (Fatiga y Adherencia)"]
    end

    subgraph Memoria [Memoria Semantica y Contexto]
        PGV[("pgvector: Embeddings de Ejercicios")]
        Hist[("Historial Clinico y RPE de Supabase")]
    end

    subgraph Inferencia [Capa de Modelos LLM]
        G_AI["Google AI Studio (Gemini Flash - Primario)"]
        OR_AI["OpenRouter (Fallback Pool)"]
        Det_AI["Generador Clinico Deterministico"]
    end

    Req --> Guard
    Guard -->|Consulta Valida| Coach
    Guard -->|Emergencia Detectada| Alerta_Emergencia["Respuesta de Seguridad Inmediata"]

    Coach --> PGV
    Coach --> Hist
    Coach --> Prev

    Coach -->|1. Intento Primario| G_AI
    G_AI -.->|Falla 429/503| OR_AI
    OR_AI -.->|Falla de Red| Det_AI

    Prev --> Alerta_Cuidador["Notificacion a Cuidador"]
```

---

## ⏳ 5. Diagrama de Estados de una Rutina Diaria (State Machine Diagram)

```mermaid
stateDiagram-v2
    [*] --> Pendiente : Generada por el sistema / IA
    Pendiente --> En_Progreso : El usuario inicia el primer ejercicio
    En_Progreso --> En_Progreso : Registro de cada ejercicio (RPE)
    En_Progreso --> Pausada_Por_Fatiga : RPE >= 9 o Dolor Agudo detectado
    Pausada_Por_Fatiga --> En_Progreso : El usuario reanuda tras descanso
    Pausada_Por_Fatiga --> Finalizada_Incompleta : El usuario decide finalizar
    En_Progreso --> Completada : Todos los ejercicios finalizados
    Completada --> [*] : Cálculo de adherencia y feedback
    Finalizada_Incompleta --> [*] : Notificación al cuidador
```
