# 👥 Issue S3-03: Agentes Especializados del Ecosistema

**Materia:** Sistemas Inteligentes  
**Docente:** Dra. Yaskelly Yedra  
**Autores:** Daniel Alejandro Sánchez Ávila & Abdenago Nahmens  
**Proyecto:** SeniorVital 2.0 — Sistemas Multiagentes y Orquestación  
**Sprint Técnico:** Sprint 3 — Arquitectura Multiagente y Supervisor Pattern  

---

## 📋 1. Catálogo y Matriz de Competencias de los Agentes

| Agente Especializado | Entrada Principal | Salida Producida | Tecnologías & Dependencias |
| :--- | :--- | :--- | :--- |
| **`WellnessCoachAgent`** | Consulta del usuario, RAG context, restricciones médicas. | Prescripción gerontológica adaptada (Nivel 1 a 4). | LangGraph, Gemini 3.6 Flash, OpenRouter, pgvector. |
| **`AnalyticsAgent`** | `senior_id`, histórico de 14 días en Supabase. | Tasa de adherencia, fatiga promedio (RPE), semáforo de riesgo (`GREEN/AMBER/RED`). | SQLAlchemy async, Supabase PostgreSQL (SQL/JSONB). |
| **`MotivationAgent`** | Nombre del paciente, tasa de adherencia, riesgo clínico. | Mensaje de refuerzo positivo no punitivo (WCAG 2.1 AA). | Heurística empática gerontológica. |
| **`QAArchitectAgent`** | Texto de respuesta sin procesar del coach. | Veredicto de aprobación (`APPROVED/SANITIZED`), lista de violaciones. | Filtros determinísticos ISO/IEC 25010 & SWEBOK v4. |

---

## 🔒 2. Límites y Reglas de Negocio Específicas

1. **Máximo 4 Niveles de Progresión:** Las rutinas nunca exceden el nivel de esfuerzo geriátrico seguro (Nivel 1: Asistido, Nivel 2: Ligero con apoyo, Nivel 3: Autocarga moderada, Nivel 4: Funcional dinámico).
2. **Modo Cuidador de Solo Lectura:** Las consultas emitidas por cuidadores activan un resumen analítico y semáforo sin alterar el plan de ejercicio del residente.
