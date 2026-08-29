# 🧠 Issue S2-03: Arquitectura de Memoria Conversacional (Short-Term & Session)

**Materia:** Sistemas Inteligentes  
**Docente:** Dra. Yaskelly Yedra  
**Autores:** Daniel Alejandro Sánchez Ávila & Abdenago Nahmens  
**Proyecto:** SeniorVital 2.0 — Agentes Inteligentes Modernos  
**Sprint Técnico:** Sprint 2 — Agentes Inteligentes, ReAct y Tool Calling  

---

## 🎯 1. Estrategia de Memoria Multinivel

Para lograr una interacción contextual fluida sin degradar los tiempos de respuesta, el sistema implementa una arquitectura de memoria en dos niveles:

```mermaid
graph TD
    User["Adulto Mayor"] --> Msg["Mensaje Entrante"]
    Msg --> STM["1. Memoria de Sesión a Corto Plazo (ConversationalMemoryManager)"]
    STM --> Win["Ventana Deslizante (Últimos 6 Turnos de Diálogo)"]
    
    Msg --> LTM["2. Memoria a Largo Plazo en Supabase (PostgreSQL + pgvector)"]
    LTM --> Prof["Perfil Clínico (senior_profiles)"]
    LTM --> Hist["Historial de Fatiga y RPE (exercise_records)"]
    LTM --> Sem["Memoria Semántica de Eventos (pgvector)"]

    Win --> ReAct["Contexto Inyectado en Ciclo ReAct"]
    Prof --> ReAct
    Hist --> ReAct
    Sem --> ReAct
```

---

## 💻 2. Implementación de `ConversationalMemoryManager`

* **Ventana Deslizante:** Retiene los últimos 6 turnos conversacionales por usuario para evitar desbordamiento del contexto del LLM.
* **Trazabilidad de Razonamiento:** Almacena junto a cada respuesta la traza de herramientas invocadas y decisiones clínicas tomadas.
* **Persistencia de Eventos:** Cualquier síntoma nuevo o dolor articular reportado se persiste asíncronamente en `exercise_records` o `health_events` en Supabase.
