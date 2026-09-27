# SeniorVital 2.0 — Plataforma Inteligente de Gestión Wellness (+60)

> **Ecosistema Basado en IA, Ingeniería del Conocimiento, Razonamiento ReAct y Sistemas Multiagentes**  
> **Maestría en Tecnologías de Información y Comunicación**  
> **La Universidad del Zulia (LUZ) — Maracaibo, Venezuela**  
> **Materia:** Sistemas Inteligentes | **Docente Titular:** Dra. Yaskelly Yedra  
> **Equipo (Team 5):** Daniel Alejandro Sánchez Ávila & Abdénago Nahmens  
> **Estado:** **Sprint 3: Sistemas Multiagentes y Orquestación (100% Completado)**  

[![CI/CD Pipeline](https://github.com/YaskCode-laboratory/wellness-platform-team5/actions/workflows/ci.yml/badge.svg)](https://github.com/YaskCode-laboratory/wellness-platform-team5/actions)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL%2015%20%2B%20pgvector-3ECF8E.svg?logo=supabase&logoColor=white)](https://supabase.com/)
[![Hugging Face](https://img.shields.io/badge/Embeddings-Hugging%20Face%20384d-FFD21E.svg?logo=huggingface&logoColor=black)](https://huggingface.co/)
[![Google AI Studio](https://img.shields.io/badge/Google%20AI%20Studio-Gemini%20Flash-4285F4.svg?logo=google&logoColor=white)](https://aistudio.google.com/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-Fallback%20Pool-6366F1.svg)](https://openrouter.ai/)
[![Render](https://img.shields.io/badge/Deploy-Render.com-46E3B7.svg?logo=render&logoColor=white)](https://seniorvital-backend.onrender.com)
[![Accessibility](https://img.shields.io/badge/Accessibility-WCAG%202.1%20AA-success.svg)](https://www.w3.org/TR/WCAG21/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## Descripción

**SeniorVital 2.0** representa la evolución de la plataforma desde un sistema transaccional estático hacia un **ecosistema multiagente inteligente asistido por Inteligencia Artificial generativa, razonamiento autónomo ReAct y recuperación aumentada por conocimiento clínico (RAG)**, diseñado para optimizar la salud motriz, nutricional y funcional en adultos mayores de 60 años.

A lo largo de sus tres fases de desarrollo consolidadas:
- **Sprint 1 (Ingeniería del Conocimiento y RAG):** Incorporación de una base ontológica clínica para 10 patologías geriátricas de alta prevalencia, segmentación semántica tripartita (`_DESC`, `_REC`, `_CONTRA`), embeddings densos en 384d e indexación vectorial HNSW en Supabase `pgvector`.
- **Sprint 2 (Agentes Inteligentes y ReAct):** Evolución hacia `WellnessCoachAgent` con ciclo iterativo de pensamiento y acción (ReAct), catálogo de herramientas clínicas (`SafetyCheckTool`, `ExerciseCatalogTool`, `RAGSearchTool`, `LogHabitTool`) y persistencia conversacional por sesión en PostgreSQL.
- **Sprint 3 (Sistemas Multiagentes y Orquestación):** Unificación arquitectónica bajo el **Patrón Supervisor Centralizado**, eliminando duplicidades y acoplamientos rígidos. El **OrchestratorAgent** clasifica intenciones y despacha dinámicamente tareas hacia el **NutritionAgent** (agente especializado desarrollado y asignado al Team 5, con herramientas de cálculo calórico/proteico y cheques clínicos de sodio/potasio/glucosa) o hacia el **WellnessCoachAgent** (ejercicios, movilidad articular y seguridad), coordinando el flujo a través de contratos formales `AgentMessage` y `DispatchRequest` con propagación unívoca de `correlation_id` hacia el endpoint `/api/v1/chat`.

> ### 🌟 Reconocimiento y Asesoría Técnica-Clínica:
> **Agradecimiento y asesoría técnica-clínica al Ing. Julio Matute por su acompañamiento en la identificación, categorización y validación de las patologías crónicas, contraindicaciones biomecánicas y guías geriátricas que fundamentan este sistema.**

---

## Objetivos

### Objetivo General
Diseñar, implementar y validar un ecosistema inteligente multiagente para la atención integral y preventiva del adulto mayor (+60), integrando recuperación semántica (RAG), razonamiento clínico ReAct y un patrón de orquestación Supervisor centralizado que despache consultas hacia agentes especializados de nutrición y bienestar físico con trazabilidad determinista y latencia optimizada.

### Objetivos Específicos (Sprint 1: RAG y Conocimiento)
1. **Modelar la Ontología Médica Geriátrica (S1-01):** Estructurar el corpus clínico en taxonomías formales con patologías, limitaciones articulares y reglas biomecánicas.
2. **Segmentar el Conocimiento con Chunking Lógico (S1-02):** Implementar la estrategia semántica tripartita preservando metadatos clínicos y niveles de progresión 1-4.
3. **Generar Representaciones Vectoriales Densas (S1-03):** Integrar embeddings de 384 dimensiones (`sentence-transformers/all-MiniLM-L6-v2`).
4. **Persistir Vectores en Supabase pgvector (S1-04):** Desplegar índices vectoriales HNSW sobre PostgreSQL relacional.
5. **Ensamblar el Pipeline RAG y Prompt Clínico (S1-05):** Orquestar la recuperación aumentada por evidencia con contingencia en OpenRouter.
6. **Validar Cuantitativamente el Rendimiento (S1-06 y S1-07):** Evaluar Hit Rate ($\ge 90\%$), MRR ($\ge 0.85$) y precisión de contraindicaciones.

### Objetivos Específicos (Sprint 2: Agentes Inteligentes y ReAct)
1. **Refactorizar y Evolucionar el Wellness Agent (S2-01 & S2-02):** Estructurar `WellnessCoachAgent` orientado a objetos en `src/`.
2. **Integrar Memoria Conversacional Persistente (S2-03):** Conectar `PostgresMemoryStore` sobre Supabase PostgreSQL por sesión.
3. **Implementar Tool Calling Autónomo y Dinámico (S2-04):** Desplegar 4 herramientas especializadas con invocación condicionada.
4. **Incorporar Patrón de Razonamiento ReAct (S2-05):** Integrar el motor Thought → Action → Observation → Final Answer con guardrails clínicos.
5. **Ejecutar Benchmark Clínico Cuantitativo (S2-06):** Validar 20 escenarios clínicos (100.0% Safety, 97.0% Tool Accuracy, 100.0% ReAct Validity).
6. **Unificar Arquitectura de Extremo a Extremo (S2-07):** Conectar `/api/v1/chat` a la arquitectura canónica de `src/` con pruebas de integración.

### Objetivos Específicos (Sprint 3: Sistemas Multiagentes y Orquestación)
1. **Clarificar el Patrón Arquitectónico Multiagente (S3-01):** Diferenciar formalmente Supervisor frente a Sequential, Hierarchical y Swarm; adoptar el **Patrón Supervisor Centralizado** y formalizar al `NutritionAgent` como desarrollo asignado al Team 5.
2. **Unificar la Orquestación y Despacho Dinámico (S3-02):** Consolidar el orquestador dinámico en `src/orchestration/`, descartando acoplamientos rígidos y soportando enrutamiento inteligente por clasificación de intenciones.
3. **Desarrollar el NutritionAgent Especializado (S3-03):** Implementar herramientas de cálculo nutricional (`NutritionCalculatorTool`) y restricciones geriátricas (`ClinicalDietaryCheckTool` para hipertensión, diabetes y salud renal).
4. **Estandarizar el Protocolo de Comunicación y Delegación (S3-04):** Conectar el endpoint `/api/v1/chat` con contratos `AgentMessage`, `DispatchRequest` y propagación de `correlation_id` extremo a extremo.
5. **Garantizar Seguridad y Persistencia en Supabase (S3-05):** Saneamiento integral de credenciales (cero secretos hardcodeados) y persistencia relacional/JSONB de sesiones y métricas en PostgreSQL.
6. **Ejecutar Benchmark Multiagente Reproducible (S3-06):** Evaluar precisión de delegación (100%), adherencia clínica geriátrica (100%) y latencias percentil 95 ($0.67\text{ ms}$).
7. **Sincronizar Documentación y Activar CI/CD Automatizado (S3-07):** Integrar ejecución obligatoria de `pytest` en GitHub Actions y sincronizar reportes e issues de auditoría.

---

## Arquitectura General

### Arquitectura Multiagente — Patrón Supervisor Centralizado (Sprint 3)

El sistema opera bajo un **Patrón Supervisor Centralizado**, donde un único componente orquestador (`OrchestratorAgent`) gobierna el ciclo de vida de la interacción: recibe la consulta del usuario, clasifica la intención (bienestar/movilidad o nutrición/hidratación), despacha la tarea al agente idóneo conservando el contexto clínico y sintetiza la respuesta con telemetría unificada.

```mermaid
flowchart TD
    User(["Adulto Mayor / Cuidador"]) -->|POST /api/v1/chat| API["FastAPI Router: /api/v1/chat"]
    
    subgraph Supervisor_Layer ["Capa de Orquestación - Patrón Supervisor Centralizado"]
        API -->|DispatchRequest + correlation_id| Orch["OrchestratorAgent (Supervisor)\nsrc/orchestration/router.py"]
        Orch --> Classifier["Clasificador de Intenciones\n(Reglas Semánticas / Fallback LLM)"]
        Classifier --> Router["Enrutador Dinámico de Dominio\nwellness | nutrition | safety | general"]
    end
    
    subgraph Specialized_Agents ["Capa de Agentes Especializados"]
        Router -->|Intención: diet / hydration| Nutri["NutritionAgent (Team 5)\nsrc/agents/nutrition/agent.py\nNutrición geriátrica, HTA y Diabetes"]
        Router -->|Intención: wellness / pain / exercises| Coach["WellnessCoachAgent\nsrc/agents/wellness/coach.py\nReAct Engine, Movilidad y Contraindicaciones"]
    end
    
    subgraph Tools_Layer ["Capa de Herramientas Clínicas"]
        Nutri --> NutriCalc["NutritionCalculatorTool\n(Calorías, Proteínas 1.2-1.5g/kg, Agua)"]
        Nutri --> DietCheck["ClinicalDietaryCheckTool\n(Filtros de Sodio, Azúcar, Potasio)"]
        Coach --> ReAct["Motor ReAct (Thought -> Action -> Observation)"]
        ReAct --> Safety["SafetyCheckTool\n(Guardrails Biomecánicos)"]
        ReAct --> RAG["RAGSearchTool\n(Supabase pgvector 384d)"]
        ReAct --> Catalog["ExerciseCatalogTool\n(Catálogo Progresivo 1-4)"]
    end
    
    subgraph Persistence_Layer ["Persistencia, Memoria y Telemetría (Supabase)"]
        Nutri -.-> DB[("Supabase PostgreSQL\nMemoria Conversacional y Perfiles")]
        Coach -.-> DB
        Orch -.-> DB
    end
    
    Nutri -->|AgentMessage: response + metadata| Orch
    Coach -->|AgentMessage: response + trace| Orch
    Orch -->|Respuesta Consolidada + correlation_id| API
    API -->|JSON Response + Telemetría| User
```

### Justificación del Patrón Supervisor Centralizado:
* **Frente al Patrón Hierarchical:** Elimina capas intermedias innecesarias de supervisores por subdominio, reduciendo la latencia de respuesta en más de un 60% y minimizando el consumo de tokens en consultas rutinarias.
* **Frente al Patrón Sequential:** Evita encadenamientos fijos donde el usuario deba pasar forzosamente por nutrición antes de consultar sobre movilidad, adaptando el despacho a la necesidad real del adulto mayor.
* **Frente al Patrón Swarm:** Proporciona gobernanza determinista, trazabilidad unívoca (`correlation_id`) y auditoría médica obligatoria antes de emitir cualquier sugerencia clínica.

---

## Tecnologías Utilizadas

| Capa Tecnológica | Tecnología / Herramienta | Función en SeniorVital 2.0 |
| :--- | :--- | :--- |
| **Backend Framework** | FastAPI 0.110.0 + Python 3.11 | API RESTful modular asíncrona |
| **Orquestación Multiagente** | Arquitectura Supervisor (Custom Engine) | Enrutamiento dinámico, contratos `AgentMessage` y `DispatchRequest` |
| **Agente Especializado Nutrición** | `NutritionAgent` (Desarrollo Team 5) | Cálculo calórico/proteico geriátrico y cheques clínicos de patologías |
| **Agente Bienestar y Movilidad** | `WellnessCoachAgent` (Motor ReAct) | Razonamiento iterativo, seguridad articular y prescripción física |
| **Persistencia Relacional y Memoria** | Supabase (PostgreSQL 15 + JSONB) | Almacenamiento de sesiones, perfiles clínicos y métricas de agentes |
| **Persistencia Vectorial** | Supabase `pgvector` (Índice HNSW) | Almacenamiento e indexación semántica de 10 patologías geriátricas |
| **Modelos de Embeddings** | Hugging Face (`all-MiniLM-L6-v2`, 384d) | Vectorización densa de conocimiento clínico |
| **Modelos LLM (Inferencia)** | Google AI Studio (`gemini-3.6-flash`) | Generación aumentada, clasificación y síntesis |
| **Cadena de Fallback** | OpenRouter (`google/gemma-4-31b:free`, `meta-llama`) | Contingencia de alta disponibilidad ante cuotas |
| **Frontend & Accesibilidad** | React 18 + Vite + Tailwind CSS | Interfaz adaptada a adultos mayores (WCAG 2.1 AA) |
| **Testing & CI/CD** | Pytest + GitHub Actions | Suite automatizada de pruebas unitarias, integración y benchmark |

---

## Estructura del Repositorio

```text
wellness-platform-team5/
├── .github/
│   └── workflows/
│       └── ci.yml                         # Pipeline CI con ejecución obligatoria de pytest
├── data/
│   ├── evaluation/
│   │   ├── coach_scenarios.json           # 20 escenarios clínicos para evaluación ReAct
│   │   ├── multiagent_scenarios.json      # 6 escenarios clínicos de delegación multiagente
│   │   ├── coach_results/                 # Métricas del agente Wellness Coach
│   │   └── multiagent_results/            # Resultados reproducibles del benchmark multiagente
│   └── knowledge_base/
│       └── clinical_knowledge_base.json   # Corpus ontológico clínico (10 patologías geriátricas)
├── docs/
│   ├── architecture/
│   │   ├── cloud-architecture.md          # Arquitectura Cloud en Render y Supabase
│   │   ├── multiagent-architecture.md     # Comparativa formal de 4 patrones y diseño Supervisor
│   │   ├── rag-architecture.md            # Arquitectura del pipeline RAG
│   │   └── system-overview.md             # Vista integral del sistema
│   ├── orchestration/
│   │   └── orchestration-pattern.md       # Especificación del Patrón Supervisor Centralizado
│   ├── reports/
│   │   ├── sprint-1-report.md             # Informe técnico ejecutivo Sprint 1
│   │   ├── sprint-2-report.md             # Informe técnico ejecutivo Sprint 2
│   │   └── sprint-3-report.md             # Informe técnico ejecutivo Sprint 3
├── issues/
│   ├── issues_sprint_1/                   # Evidencias y auditoría del Sprint 1 (S1-01 a S1-07)
│   ├── issues_sprint_2/                   # Evidencias y auditoría del Sprint 2 (S2-01 a S2-07)
│   └── issues_sprint_3/                   # Evidencias y auditoría del Sprint 3 (S3-01 a S3-07)
├── scripts/
│   ├── evaluation/
│   │   ├── evaluate_coach.py              # Benchmark del agente ReAct (Sprint 2)
│   │   └── evaluate_multiagent.py         # Benchmark de delegación, latencia y adherencia (Sprint 3)
│   └── ingestion/
│       └── ingest_knowledge.py            # Ingesta e indexación en Supabase pgvector
├── src/
│   ├── agents/
│   │   ├── nutrition/                     # NutritionAgent (Team 5): cálculo nutricional y cheques
│   │   │   ├── agent.py                   # Lógica de agente y manejo de condiciones geriátricas
│   │   │   └── tools.py                   # NutritionCalculatorTool y ClinicalDietaryCheckTool
│   │   └── wellness/                      # WellnessCoachAgent: razonamiento ReAct y coach físico
│   ├── api/
│   │   ├── chat.py                        # Endpoint /api/v1/chat conectado al Supervisor
│   │   ├── config.py                      # Configuración segura de entorno (cero secretos)
│   │   └── main.py                        # Punto de entrada de FastAPI
│   ├── memory/
│   │   └── postgres_store.py              # Memoria conversacional sobre Supabase PostgreSQL
│   ├── orchestration/                     # Motor de orquestación canónico (Única fuente de verdad)
│   │   ├── contracts.py                   # Contratos AgentMessage, DispatchRequest, WorkflowContext
│   │   ├── engine.py                      # Motor de flujos de trabajo WorkflowEngine
│   │   └── router.py                      # Enrutador Supervisor y clasificador de intenciones
│   ├── rag/                               # Pipeline RAG, embeddings y pgvector
│   └── tools/                             # Herramientas clínicas (SafetyCheck, Catalog, RAG)
└── tests/
    ├── agents/                            # Pruebas unitarias de agentes (Wellness y Nutrition)
    ├── integration/                       # Pruebas de integración del endpoint chat y flujos
    ├── multiagent/                        # Pruebas del orquestador y protocolos de despacho
    └── rag/                               # Pruebas del pipeline RAG y embeddings
```

---

## 🎯 Matriz de Trazabilidad de Entregables (Sprint 3: Sistemas Multiagentes)

| Issue | Descripción del Entregable | Módulo / Ubicación en Repositorio | Estado |
| :---: | :--- | :--- | :---: |
| **`S3-01`** | **Clarificación del Patrón Arquitectónico Multiagente:** Diferenciación formal de 4 patrones (Supervisor, Sequential, Hierarchical, Swarm), adopción del Patrón Supervisor Centralizado y formalización del `NutritionAgent` como componente asignado al Team 5. | `docs/architecture/multiagent-architecture.md`<br/>`docs/orchestration/orchestration-pattern.md`<br/>[`issues/issues_sprint_3/S3-01_Arquitectura_Multiagente.md`](issues/issues_sprint_3/S3-01_Arquitectura_Multiagente.md) | ✅ **100%** (Aprobado y Validado) |
| **`S3-02`** | **Unificación de la Orquestación bajo el Patrón Supervisor:** Eliminación de pipelines rígidos legacy en `app/`, consolidación en `src/orchestration/` y enrutamiento inteligente por intención hacia agentes especializados. | `src/orchestration/router.py`<br/>`src/orchestration/engine.py`<br/>[`issues/issues_sprint_3/S3-02_Orchestrator_Agent.md`](issues/issues_sprint_3/S3-02_Orchestrator_Agent.md) | ✅ **100%** (Aprobado y Validado) |
| **`S3-03`** | **Implementación y Evidencia del NutritionAgent (Team 5):** Desarrollo completo del agente especializado en nutrición geriátrica con herramientas de cálculo (`NutritionCalculatorTool`) y restricciones clínicas (`ClinicalDietaryCheckTool` para diabetes e HTA). | `src/agents/nutrition/`<br/>[`issues/issues_sprint_3/S3-03_Agente_Especializado.md`](issues/issues_sprint_3/S3-03_Agente_Especializado.md)<br/>[`issues/issues_sprint_3/S3-03_Agentes_Especializados.md`](issues/issues_sprint_3/S3-03_Agentes_Especializados.md) | ✅ **100%** (Aprobado y Validado) |
| **`S3-04`** | **Protocolo de Comunicación y Conexión de Endpoint Chat:** Conexión de `/api/v1/chat` al Supervisor mediante contratos formales `AgentMessage`, `DispatchRequest` y propagación de `correlation_id` de extremo a extremo. | `src/api/chat.py`<br/>`src/orchestration/contracts.py`<br/>[`issues/issues_sprint_3/S3-04_Comunicacion_Delegacion.md`](issues/issues_sprint_3/S3-04_Comunicacion_Delegacion.md) | ✅ **100%** (Aprobado y Validado) |
| **`S3-05`** | **Seguridad y Persistencia en Supabase:** Auditoría y saneamiento total de credenciales (eliminación de contraseñas hardcodeadas), carga vía variables de entorno y documentación de consultas SQL/JSONB en PostgreSQL. | `src/api/config.py`<br/>`seniorvital_shared/db.py`<br/>[`issues/issues_sprint_3/S3-05_Integracion_Datos.md`](issues/issues_sprint_3/S3-05_Integracion_Datos.md)<br/>[`issues/issues_sprint_3/S3-05_Integracion_Supabase.md`](issues/issues_sprint_3/S3-05_Integracion_Supabase.md) | ✅ **100%** (Aprobado y Validado) |
| **`S3-06`** | **Evaluación Cuantitativa y Benchmark Multiagente:** Script reproducible `evaluate_multiagent.py` evaluando precisión de enrutamiento (100%), latencias (Media 0.31ms, P95 0.67ms) y adherencia clínica geriátrica (100%). | `scripts/evaluation/evaluate_multiagent.py`<br/>`data/evaluation/multiagent_results/`<br/>[`issues/issues_sprint_3/S3-06_Evaluacion_Multiagente.md`](issues/issues_sprint_3/S3-06_Evaluacion_Multiagente.md) | ✅ **100%** (Aprobado y Validado) |
| **`S3-07`** | **Sincronización Documental y Activación CI/CD:** Activación obligatoria de `pytest` en GitHub Actions (`ci.yml`), sincronización completa del `README.md` con diagramas de flujo y cierre de auditorías S3-01 a S3-07. | `.github/workflows/ci.yml`<br/>`README.md`<br/>`docs/reports/sprint-3-report.md`<br/>[`issues/issues_sprint_3/S3-07_Documentacion_Demo.md`](issues/issues_sprint_3/S3-07_Documentacion_Demo.md) | ✅ **100%** (Aprobado y Validado) |

---

## 🎯 Matriz de Trazabilidad de Entregables (Sprint 2: Agentes Inteligentes)

| Issue | Descripción del Entregable | Módulo / Ubicación en Repositorio | Estado |
| :---: | :--- | :--- | :---: |
| **`S2-01`** | **Refactorización del Wellness Coach hacia Agente Inteligente:** Migración desde agente estático a arquitectura ReAct orientada a objetos en `src/`. | `src/agents/wellness/coach.py`<br/>[`issues/issues_sprint_2/S2-01_Refactorizacion_Wellness_Agent.md`](issues/issues_sprint_2/S2-01_Refactorizacion_Wellness_Agent.md) | ✅ **100%** (Completado) |
| **`S2-02`** | **Diseño y Herencia del Wellness Coach 2.0:** Herencia formal de `WellnessAgent`, orquestación de herramientas y depuración de llamadas residuales legacy. | `src/agents/wellness/coach.py`<br/>`src/agents/wellness/agent.py`<br/>[`issues/issues_sprint_2/S2-02_Diseno_Wellness_Coach_2.0.md`](issues/issues_sprint_2/S2-02_Diseno_Wellness_Coach_2.0.md) | ✅ **100%** (Completado) |
| **`S2-03`** | **Memoria Conversacional Persistente:** Persistencia de mensajes en Supabase PostgreSQL con `PostgresMemoryStore`, eliminando estado volátil en RAM. | `src/memory/postgres_store.py`<br/>[`issues/issues_sprint_2/S2-03_Memoria_Conversacional.md`](issues/issues_sprint_2/S2-03_Memoria_Conversacional.md) | ✅ **100%** (Completado) |
| **`S2-04`** | **Tool Calling Dinámico e Integración:** Catálogo de 4 herramientas especializadas (`SafetyCheckTool`, `ExerciseCatalogTool`, `RAGSearchTool`, `LogHabitTool`) invocadas autónomamente. | `src/tools/wellness/`<br/>[`issues/issues_sprint_2/S2-04_Tool_Calling_Integracion.md`](issues/issues_sprint_2/S2-04_Tool_Calling_Integracion.md) | ✅ **100%** (Completado) |
| **`S2-05`** | **Patrón de Razonamiento ReAct:** Motor iterativo Thought → Action → Observation → Final Answer con guardrails de seguridad. | `src/agents/wellness/reasoning.py`<br/>[`issues/issues_sprint_2/S2-05_Patron_ReAct.md`](issues/issues_sprint_2/S2-05_Patron_ReAct.md) | ✅ **100%** (Completado) |
| **`S2-06`** | **Evaluación Cuantitativa del Agente:** Suite completa de 20 escenarios clínicos con 100.0% Safety Compliance y 97.0% Tool Accuracy. | `scripts/evaluation/evaluate_coach.py`<br/>`data/evaluation/coach_results/metrics_summary.json`<br/>[`issues/issues_sprint_2/S2-06_Evaluacion_Agente.md`](issues/issues_sprint_2/S2-06_Evaluacion_Agente.md) | ✅ **100%** (Completado) |
| **`S2-07`** | **Arquitectura Integral y Endpoint /chat:** Conexión de extremo a extremo en FastAPI (`/api/v1/chat`), validación de integración (`test_chat_endpoint.py`) y sincronización documental. | `src/api/chat.py`<br/>`tests/integration/test_chat_endpoint.py`<br/>[`issues/issues_sprint_2/S2-07_Arquitectura_Resultados.md`](issues/issues_sprint_2/S2-07_Arquitectura_Resultados.md) | ✅ **100%** (Completado) |

---

## 🎯 Matriz de Trazabilidad de Entregables (Sprint 1: RAG y Conocimiento)

| Issue | Descripción del Entregable | Módulo / Ubicación en Repositorio | Estado |
| :---: | :--- | :--- | :---: |
| **`S1-01`** | **Base de Conocimiento y Ontología Médica:** Modelado de 10 patologías geriátricas, restricciones biomecánicas y reconocimiento al Ing. Julio Matute. | `data/knowledge_base/`<br/>`docs/knowledge/`<br/>[`issues/issues_sprint_1/S1-01_Base_Conocimiento.md`](issues/issues_sprint_1/S1-01_Base_Conocimiento.md) | ✅ **100%** (Aprobado) |
| **`S1-02`** | **Estrategia de Segmentación Lógica (Chunking):** Chunking semántico tripartito (`_DESC`, `_REC`, `_CONTRA`) preservando niveles de progresión segura (1-4). | `src/knowledge/chunking/chunker.py`<br/>`docs/rag/chunking-strategy.md`<br/>[`issues/issues_sprint_1/S1-02_Estrategia_Chunking.md`](issues/issues_sprint_1/S1-02_Estrategia_Chunking.md) | ✅ **100%** (Aprobado) |
| **`S1-03`** | **Generación de Representaciones Vectoriales (Embeddings):** Vectorización densa (384d) vía Hugging Face real y aserción estricta (`HUGGINGFACE_REAL_MODEL`). | `src/rag/embeddings/hf_embeddings.py`<br/>`docs/rag/embeddings-strategy.md`<br/>[`issues/issues_sprint_1/S1-03_Embeddings.md`](issues/issues_sprint_1/S1-03_Embeddings.md) | ✅ **100%** (Corregido y Verificado) |
| **`S1-04`** | **Base de Datos Vectorial con pgvector:** Almacenamiento en Supabase PostgreSQL con índice `HNSW` y similitud de coseno. | `src/rag/vector_store/pgvector_store.py`<br/>`docs/rag/vector-database.md`<br/>[`issues/issues_sprint_1/S1-04_Base_Vectorial_pgvector.md`](issues/issues_sprint_1/S1-04_Base_Vectorial_pgvector.md) | ✅ **100%** (Aprobado) |
| **`S1-05`** | **Pipeline RAG Integrado:** Orquestación de consulta, recuperación semántica y prompt clínico aumentado con telemetría unívoca. | `src/rag/pipeline/rag_pipeline.py`<br/>`src/rag/retriever/retriever.py`<br/>[`issues/issues_sprint_1/S1-05_Pipeline_RAG.md`](issues/issues_sprint_1/S1-05_Pipeline_RAG.md) | ✅ **100%** (Corregido y Verificado) |
| **`S1-06`** | **Evaluación Cuantitativa y QA:** Suite de tests automatizados, métricas de recuperación recalculadas (Hit Rate 100%, MRR 0.9000, P@3 0.6333) y telemetría de latencias. | `tests/rag/`<br/>`docs/evaluation/retrieval-metrics.md`<br/>[`issues/issues_sprint_1/S1-06_Evaluacion_QA.md`](issues/issues_sprint_1/S1-06_Evaluacion_QA.md) | ✅ **100%** (Corregido y Verificado) |
| **`S1-07`** | **Arquitectura RAG Consolidada:** Documentación arquitectónica consolidada, distinción formal de telemetría y purga terminológica metodológica. | `docs/architecture/rag-architecture.md`<br/>`docs/reports/sprint-1-report.md`<br/>[`issues/issues_sprint_1/S1-07_Arquitectura_RAG.md`](issues/issues_sprint_1/S1-07_Arquitectura_RAG.md) | ✅ **100%** (Corregido y Consolidado) |

---

## Instalación y Ejecución (Guía de Reproducibilidad)

Sigue estos pasos para clonar, ejecutar la ingesta, levantar la plataforma y validar las pruebas automatizadas del ecosistema multiagente:

### 1. Clonar el repositorio y posicionarse en la rama del sprint
```bash
git clone https://github.com/YaskCode-laboratory/wellness-platform-team5.git
cd wellness-platform-team5
git checkout sprint-3
```

### 2. Configurar el entorno virtual e instalar dependencias
```bash
# Crear entorno virtual de Python 3.11
python -m venv venv

# Activar entorno virtual
# En Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# En Linux / macOS:
source venv/bin/activate

# Instalar dependencias del proyecto
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configurar variables de entorno
Copia la plantilla de configuración e ingresa tus credenciales (sin exponerlas en el control de versiones):
```bash
cp .env.example .env
```
> **Variables requeridas en `.env`:**
> ```ini
> DATABASE_URL=postgresql+asyncpg://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
> GEMINI_API_KEY=your_google_ai_studio_key_here
> OPENROUTER_API_KEY=your_openrouter_key_here
> HF_TOKEN=your_huggingface_token_here
> ENVIRONMENT=development
> ```

### 4. Ejecutar la ingesta y vectorización del conocimiento clínico
```bash
python scripts/ingestion/ingest_knowledge.py
```

### 5. Ejecutar la suite completa de pruebas automatizadas en CI
```bash
python -m pytest tests/ -v --ignore=tests/legacy/
```
*Salida esperada:*
```text
============================== 237 passed, 37 skipped in 72.45s ==============================
```

### 6. Ejecutar el benchmark multiagente (Precisión de Enrutamiento y Calidad Clínica)
```bash
python scripts/evaluation/evaluate_multiagent.py
```
*Salida esperada:*
```text
Delegation Accuracy:      100.0% (6/6)
Clinical Adherence Rate:  100.0% (6/6)
Critical Safety Block:    100.0%
Latency Mean:             0.31 ms
Latency P95:              0.67 ms
```

### 7. Ejecución de la API Backend y Frontend
```bash
# Iniciar Servidor FastAPI
uvicorn src.api.main:app --reload --port 8000
# Swagger UI interactivo disponible en: http://localhost:8000/docs

# Iniciar Frontend (en otra terminal)
cd src/app
npm install
npm run dev
# Aplicación web disponible en: http://localhost:5173
```

---

## 📑 Índice de Documentación Viva

### Sprint 3: Sistemas Multiagentes y Orquestación Supervisor
* 🏛️ **Arquitectura Multiagente Formal:** [`docs/architecture/multiagent-architecture.md`](docs/architecture/multiagent-architecture.md)
* 🔄 **Especificación del Patrón Supervisor:** [`docs/orchestration/orchestration-pattern.md`](docs/orchestration/orchestration-pattern.md)
* 🥗 **NutritionAgent (Team 5):** [`issues/issues_sprint_3/S3-03_Agente_Especializado.md`](issues/issues_sprint_3/S3-03_Agente_Especializado.md)
* 📊 **Resultados del Benchmark Multiagente:** [`data/evaluation/multiagent_results/multiagent_benchmark_results.json`](data/evaluation/multiagent_results/multiagent_benchmark_results.json)
* 📋 **Informe Ejecutivo Sprint 3:** [`docs/reports/sprint-3-report.md`](docs/reports/sprint-3-report.md)
* 📂 **Evidencias de Issues (S3-01 a S3-07):** [`issues/issues_sprint_3/`](issues/issues_sprint_3/)

### Sprint 2: Agentes Inteligentes, ReAct y Tool Calling
* 🤖 **Arquitectura del Wellness Coach Agent:** [`docs/agents/wellness-agent.md`](docs/agents/wellness-agent.md)
* 📊 **Evaluación Cuantitativa y Benchmark (20 Escenarios):** [`data/evaluation/coach_results/metrics_summary.json`](data/evaluation/coach_results/metrics_summary.json)
* 📋 **Informe Ejecutivo Sprint 2:** [`docs/reports/sprint-2-report.md`](docs/reports/sprint-2-report.md)
* 📂 **Evidencias de Issues (S2-01 a S2-07):** [`issues/issues_sprint_2/`](issues/issues_sprint_2/)

### Sprint 1: Ingeniería del Conocimiento y RAG
* 🗺️ **Mapa de Dominio:** [`docs/knowledge/domain-map.md`](docs/knowledge/domain-map.md)
* 🧬 **Ontología Médica:** [`docs/knowledge/ontology.md`](docs/knowledge/ontology.md)
* 📊 **Taxonomía de Ejercicios:** [`docs/knowledge/taxonomy.md`](docs/knowledge/taxonomy.md)
* 📚 **Fuentes Bibliográficas & Asesoría Clínica:** [`docs/rag/knowledge-sources.md`](docs/rag/knowledge-sources.md)
* ✂️ **Estrategia de Chunking:** [`docs/rag/chunking-strategy.md`](docs/rag/chunking-strategy.md)
* 🧬 **Estrategia de Embeddings:** [`docs/rag/embeddings-strategy.md`](docs/rag/embeddings-strategy.md)
* 🗄️ **Base de Datos Vectorial (pgvector):** [`docs/rag/vector-database.md`](docs/rag/vector-database.md)
* 🏛️ **Arquitectura del Pipeline RAG:** [`docs/architecture/rag-architecture.md`](docs/architecture/rag-architecture.md)
* 📈 **Métricas de Evaluación RAG:** [`docs/evaluation/retrieval-metrics.md`](docs/evaluation/retrieval-metrics.md)
* 📋 **Informe Ejecutivo Sprint 1:** [`docs/reports/sprint-1-report.md`](docs/reports/sprint-1-report.md)
* 📂 **Evidencias de Issues (S1-01 a S1-07):** [`issues/issues_sprint_1/`](issues/issues_sprint_1/)

---

## Equipo

* **Daniel Alejandro Sánchez Ávila** — *Investigador y Desarrollador Backend / DevOps*
* **Abdénago Nahmens** — *Investigador y Desarrollador Frontend / UX-UI*
* **Dra. Yaskelly Yedra** — *Tutor Académico y Docente Titular de la Asignatura*
* **Ing. Julio Matute** — *Asesor Técnico-Clínico Gerontológico*

---

## Estado del Proyecto

* **Fase Actual:** **Sprint 3: Sistemas Multiagentes y Orquestación (Completado al 100% / 45% del Proyecto Total).**
* **Hitos Consolidados:**
  - Base de conocimiento de 10 patologías geriátricas y RAG integrado (Sprint 1).
  - `WellnessCoachAgent` con herencia formal de `WellnessAgent`, Tool Calling y ciclo ReAct en `src/` (Sprint 2).
  - Conexión de `PostgresMemoryStore` sobre Supabase PostgreSQL por sesión de usuario (Sprint 2).
  - Unificación bajo el **Patrón Supervisor Centralizado** en `src/orchestration/`, descartando acoplamientos rígidos legacy (Sprint 3).
  - Desarrollo del **NutritionAgent** (especializado para Team 5) con herramientas de cálculo y cheques de patologías geriátricas (Sprint 3).
  - Integración del endpoint `/api/v1/chat` con enrutamiento dinámico, contratos `AgentMessage`, `DispatchRequest` y propagación de `correlation_id` (Sprint 3).
  - Ejecución de benchmark multiagente con 100% de precisión de delegación y 100% de adherencia clínica (Sprint 3).
  - Activación obligatoria de `pytest` en CI de GitHub Actions y saneamiento total de credenciales (Sprint 3).
* **Próxima Fase:** **Sprint 4: Integración Avanzada, Monitoreo Continuo y Despliegue en Producción.**
