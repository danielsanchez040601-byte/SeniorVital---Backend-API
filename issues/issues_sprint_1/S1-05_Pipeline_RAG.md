# 🚀 Issue S1-05: Pipeline RAG y Generación Aumentada con Contexto Clínico

**Materia:** Sistemas Inteligentes  
**Docente:** Dra. Yaskelly Yedra  
**Autores:** Daniel Alejandro Sánchez Ávila & Abdenago Nahmens  
**Proyecto:** SeniorVital 2.0 — Sistema RAG Gerontológico  
**Sprint Técnico:** Sprint 1 — Ingeniería del Conocimiento y Sistemas RAG  

---

## 🎯 1. Flujo Integral del Pipeline RAG

El pipeline de **Generación Aumentada por Recuperación (RAG)** de SeniorVital consta de cuatro etapas deterministas:

```mermaid
sequenceDiagram
    autonumber
    actor Usuario as Adulto Mayor / Cuidador
    participant API as FastAPI Router (/api/v1/chat o /routines/generate)
    participant RAG as RAG Processor (rag_processor.py)
    participant HF as Hugging Face Embedder (384d)
    participant PGV as Supabase pgvector (clinical_knowledge)
    participant Guard as Guardrails Clínicos
    participant LLM as Google AI Studio (gemini-3.6-flash) / OpenRouter

    Usuario->>API: Consulta o Solicitud de Rutina
    API->>RAG: generate_rag_response(query, user_profile)
    
    RAG->>HF: embed_query(query_text)
    HF-->>RAG: vector_384d
    
    RAG->>PGV: match_clinical_knowledge(vector_384d, limit=3)
    PGV-->>RAG: Chunks Clínicos Relevantes (Evidencia + Contraindicaciones)
    
    RAG->>Guard: Evaluar seguridad clínica del prompt
    alt Emergencia Vital Detectada (Dolor en pecho / Caída aguda)
        Guard-->>RAG: Bloqueo de seguridad inmediato
        RAG-->>API: Respuesta de derivación a emergencias
    else Consulta Segura
        Guard-->>RAG: Inyectar System Prompt + Contexto Recuperado
        RAG->>LLM: Inferencia con Prompt Enriquecido
        LLM-->>RAG: Respuesta Médicamente Fundamentada
        RAG-->>API: Respuesta al Usuario
    end
    
    API-->>Usuario: HTTP 200 OK con Recomendación Segura
```

---

## 📝 2. Estructura del Prompt Aumentado con Contexto RAG

```text
[ROL Y DIRECTIVAS CLÍNICAS]
Eres "SeniorVital Wellness Coach", un asistente clínico de gerontología y fisioterapia geriátrica.
Tu misión es brindar recomendaciones de movimiento y bienestar estrictamente seguras para adultos mayores de 60 años.

[CONTEXTO CLÍNICO RECUPERADO DE LA BASE DE CONOCIMIENTO (RAG)]:
---
Condición: {condicion_recuperada}
Categoría: {categoria_recuperada}
Evidencia y Plan: {contenido_texto}
Contraindicaciones Estrictas: {contraindicaciones}
Fuente: {metadata_fuente}
---

[PERFIL DEL ADULTO MAYOR]:
- Nombre: Carlos Mendoza
- Nivel de Condición Física: 1 (Básico / Sedentario)
- Patologías Reportadas: Osteoartritis de Rodilla
- Último Esfuerzo RPE: 4 (Moderado)

[CONSULTA DEL USUARIO]:
"{query_usuario}"

[REGLAS INQUEBRANTABLES]:
1. Si el usuario reporta dolor articular agudo o emergencia vital, ordena detener el ejercicio y consultar a urgencias.
2. Nunca sugieras saltos (pliometría), flexiones de rodilla mayores a 90 grados ni maniobra de Valsalva.
3. Responde con calidez, empatía y lenguaje sencillo y claro.
```
