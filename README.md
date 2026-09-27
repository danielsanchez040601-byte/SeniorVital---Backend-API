# SeniorVital 2.0 — Plataforma Inteligente de Gestión Wellness (+60)

> **Ecosistema Basado en IA, Ingeniería del Conocimiento y Sistemas RAG**  
> **Maestría en Tecnologías de Información y Comunicación**  
> **La Universidad del Zulia (LUZ) — Maracaibo, Venezuela**  
> **Materia:** Sistemas Inteligentes | **Docente Titular:** Dra. Yaskelly Yedra  
> **Equipo (Team 5):** Daniel Alejandro Sánchez Ávila & Abdénago Nahmens  
> **Estado:** **Sprint 2: Agentes Inteligentes, ReAct y Tool Calling (100% Completado)**  

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

**SeniorVital 2.0** representa la evolución de la plataforma desde un sistema transaccional estático hacia un **sistema inteligente asistido por Inteligencia Artificial generativa y recuperación aumentada por conocimiento clínico (RAG)**, diseñado para optimizar la salud motriz, prevenir la fragilidad y mitigar el deterioro funcional en adultos mayores de 60 años.

En esta fase (*Sprint 1*), la plataforma incorpora una base de conocimiento ontológica formalizada que modela las principales patologías geriátricas de alta prevalencia: **osteoartritis de rodilla y cadera, sarcopenia, dinapenia, osteoporosis, insuficiencia cardíaca crónica, EPOC, hipertensión arterial, Parkinson y secuelas de ACV**. A través de un motor RAG serverless, el sistema recupera de manera determinística las reglas de dosificación física y los **filtros duros de contraindicación biomecánica** (ej. prohibición de saltos, flexiones profundas $>90^\circ$ o flexiones espinales con carga), garantizando que las recomendaciones de ejercicio estén condicionadas por reglas clínicas, guardrails y evidencia recuperada del dominio, adaptándose al nivel de autonomía del usuario.

> ### 🌟 Reconocimiento y Asesoría Técnica-Clínica:
> **Agradecimiento y asesoría técnica-clínica al Ing. Julio Matute por su acompañamiento en la identificación, categorización y validación de las patologías crónicas y afecciones funcionales de adultos mayores que fundamentan esta base de conocimiento.**

---

## Objetivos

### Objetivo General
Estructurar, implementar y evaluar la arquitectura de **Ingeniería del Conocimiento y Recuperación Aumentada por Generación (RAG)** de SeniorVital 2.0, permitiendo la indexación vectorial y la recuperación semántica precisa de directrices clínicas para la prescripción gerontológica segura.

### Objetivos Específicos (Sprint 1)
1. **Modelar la Ontología Médica Geriátrica (S1-01):** Estructurar el corpus clínico en taxonomías y esquemas formales que relacionen patologías, limitaciones articulares y reglas de contraindicación biomecánica.
2. **Segmentar el Conocimiento con Chunking Lógico (S1-02):** Implementar una estrategia de partición semántica tripartita (perfil clínico, prescripción recomendada y filtros de seguridad) preservando metadatos.
3. **Generar Representaciones Vectoriales Densas (S1-03):** Integrar modelos de embeddings de 384 dimensiones (`sentence-transformers/all-MiniLM-L6-v2`) con latencia reducida.
4. **Persistir Vectores en Supabase pgvector (S1-04):** Desplegar índices vectoriales `HNSW` en PostgreSQL gestionado, optimizando la búsqueda por similitud de coseno ($1 - \cos(\theta)$).
5. **Ensamblar el Pipeline RAG y Prompt Clínico (S1-05):** Orquestar la recuperación semántica filtrada y el aumento contextual para los modelos LLM (Google AI Studio con fallback en OpenRouter).
6. **Validar Cuantitativamente el Rendimiento (S1-06 y S1-07):** Evaluar la tasa de acierto (Hit Rate $\ge 90\%$), Mean Reciprocal Rank (MRR $\ge 0.85$) y precisión de contraindicaciones mediante pruebas automatizadas.

### Objetivos Específicos (Sprint 2)
1. **Refactorizar y Evolucionar el Wellness Agent (S2-01 & S2-02):** Estructurar `WellnessCoachAgent` con herencia formal de `WellnessAgent`, desacoplando la orquestación e integrando `src/` como única fuente de verdad.
2. **Integrar Memoria Conversacional Persistente (S2-03):** Conectar `PostgresMemoryStore` sobre Supabase PostgreSQL para retención contextual por sesión, eliminando estado volátil en RAM.
3. **Implementar Tool Calling Autónomo y Dinámico (S2-04):** Desplegar 4 herramientas especializadas (`SafetyCheckTool`, `ExerciseCatalogTool`, `RAGSearchTool`, `LogHabitTool`) con invocación condicionada a la intención del usuario.
4. **Incorporar Patrón de Razonamiento ReAct (S2-05):** Integrar el motor iterativo Thought → Action → Observation → Final Answer en `reasoning.py` con guardrails de seguridad y control de ciclos.
5. **Ejecutar Benchmark Clínico Cuantitativo (S2-06):** Validar la suite completa de 20 escenarios clínicos con cálculo riguroso de Safety Compliance (100.0%), Tool Accuracy (97.0%) y ReAct Validity (100.0%).
6. **Unificar Arquitectura de Extremo a Extremo (S2-07):** Conectar el endpoint `/api/v1/chat` a la arquitectura canónica de `src/`, respaldado por pruebas de integración automatizadas (`TestClient`) con mocks deterministas.


---

## Arquitectura general

La arquitectura de **SeniorVital 2.0 (Sprint 1)** implementa un pipeline RAG desacoplado, *Open Source* y *Cloud-Native*, que traslada el conocimiento clínico hacia una base vectorial relacional en **Supabase (`pgvector`)**, alimentando los modelos de lenguaje mediante inferencia híbrida:

```mermaid
flowchart TD
    subgraph Ingesta_Knowledge [Ingesta y Procesamiento de Conocimiento]
        Doc["Base Documental Clinica - 10 Patologias Geriatricas"]
        Chunker["Segmentador Semantico Tripartito - src/knowledge/chunking/"]
        HF_Embed["Generador de Embeddings 384d - Hugging Face"]
        
        Doc --> Chunker
        Chunker -->|Metadata: _DESC, _REC, _CONTRA| HF_Embed
    end

    subgraph Vector_Storage [Persistencia Vectorial Relacional]
        PGV[("Supabase PostgreSQL y pgvector - Indice HNSW")]
    end

    subgraph RAG_Runtime [Runtime de Recuperacion y Generacion]
        Query["Perfil del Adulto Mayor - Patologias y Nivel 1-4"]
        Retriever["Recuperador Semantico - src/rag/retriever/"]
        Context["Ensamblador de Contexto y Guardrails"]
        Prompt["Prompt Clinico Aumentado con Evidencia"]
        
        LLM_Primary["Google AI Studio - Gemini Flash Primario"]
        LLM_Fallback["OpenRouter - Fallback Pool Contingencia"]
        Response["Prescripcion Segura de Ejercicios"]
        
        Query --> Retriever
        Retriever --> Context
        Context --> Prompt
        Prompt --> LLM_Primary
        LLM_Primary -.->|Fallback por saturacion| LLM_Fallback
        LLM_Primary --> Response
        LLM_Fallback --> Response
    end

    HF_Embed -->|Almacenamiento Vectores 384d| PGV
    Retriever -->|Busqueda por Similitud Coseno Top-K=3| PGV
    PGV -->|Fragmentos Clinicos Relevantes| Retriever
```

### Justificación del Stack Tecnológico:
* **Desacoplamiento Serverless ($0 FinOps):** Se descartan soluciones propietarias bloqueantes (GCP Vertex AI Search / Chroma local) en favor de **Supabase PostgreSQL con extensión nativa `pgvector`**, lo que permite almacenar los perfiles transaccionales y los vectores de conocimiento en una sola base de datos ACID.
* **Embeddings Eficientes (384d):** `sentence-transformers/all-MiniLM-L6-v2` provee alta fidelidad semántica en español/inglés con un consumo de almacenamiento de solo $1.5\text{ KB}$ por vector indexado.
* **Inferencia Híbrida Resiliente:** Google AI Studio (`gemini-3.6-flash`) como motor de generación primario de ultra-baja latencia, respaldado por un pool de contingencia en OpenRouter.

---

## Tecnologías utilizadas

| Capa Tecnológica | Tecnología / Herramienta | Función en SeniorVital 2.0 |
| :--- | :--- | :--- |
| **Backend Framework** | FastAPI 0.110.0 + Python 3.11 | API RESTful modular asíncrona |
| **Persistencia Vectorial** | Supabase (PostgreSQL 15 + `pgvector`) | Almacenamiento e indexación vectorial HNSW |
| **Modelos de Embeddings** | Hugging Face (`all-MiniLM-L6-v2`, 384d) | Vectorización semántica de textos clínicos |
| **Modelos LLM (Inferencia)** | Google AI Studio (`gemini-3.6-flash`) | Generación aumentada y razonamiento clínico |
| **Cadena de Fallback** | OpenRouter (`google/gemma-4-31b:free`, `meta-llama`) | Pool de contingencia ante saturación de cuota |
| **Frontend & Accesibilidad** | React 18 + Vite + Tailwind CSS | UI gerontológica (WCAG 2.1 AA, Touch $\ge 48\text{px}$) |
| **Testing & Calidad** | Pytest + Pytest-Asyncio | Pruebas unitarias de chunking, embeddings y retrieval |
| **DevOps & CI/CD** | GitHub Actions + Docker + Render.com | Pipeline automatizado y despliegue continuo |

---

## Estructura del repositorio

```text
wellness-platform-team5/
├── data/
│   └── knowledge_base/
│       └── clinical_knowledge_base.json   # Corpus clínico estructurado (10 patologías y reglas)
├── docs/
│   ├── architecture/
│   │   ├── cloud-architecture.md          # Arquitectura de despliegue cloud en Render y Supabase
│   │   ├── data-architecture.md           # Modelo relacional y esquemas DDL
│   │   └── system-overview.md             # Diagramas UML y arquitectura del sistema
│   ├── evaluation/
│   │   └── retrieval-metrics.md           # Métricas cuantitativas (Hit Rate, MRR, Precision)
│   ├── knowledge/
│   │   ├── domain-map.md                  # Mapa conceptual del dominio gerontológico
│   │   ├── knowledge-sources.md           # Bibliografía médica y reconocimiento al Ing. Julio Matute
│   │   ├── ontology.md                    # Ontología formal de patologías y contraindicaciones
│   │   └── taxonomy.md                    # Taxonomía jerárquica de ejercicios geriátricos
│   ├── project/
│   │   ├── scope.md                       # Alcance funcional y delimitación
│   │   └── team.md                        # Identificación del equipo de investigación LUZ
│   ├── rag/
│   │   ├── chunking-strategy.md           # Estrategia de segmentación lógica tripartita
│   │   ├── embeddings-strategy.md         # Modelo y dimensionalidad de representación vectorial
│   │   ├── rag-architecture.md            # Diagrama y flujo del pipeline RAG
│   │   └── vector-database.md             # DDL e indexación HNSW con pgvector
│   ├── reports/
│   │   └── sprint-1-report.md             # Informe técnico ejecutivo del Sprint 1
│   └── requirements/
│       ├── functional-requirements.md     # Requisitos funcionales del sistema (RF-01 a RF-10)
│       ├── non-functional-requirements.md # Modelo de calidad ISO/IEC 25010 y WCAG 2.1 AA
│       ├── use-cases.md                  # Especificación de casos de uso (CU-01 a CU-08)
│       └── user-stories.md               # Historias de usuario en formato Gherkin
├── issues/
│   └── issues_sprint_1/
│       ├── S1-01_Base_Conocimiento.md     # Evidencia y diseño de ontología clínica
│       ├── S1-02_Estrategia_Chunking.md   # Evidencia de segmentación semántica
│       ├── S1-03_Embeddings.md            # Evidencia de representación vectorial
│       ├── S1-04_Base_Vectorial_pgvector.md # Evidencia de persistencia en Supabase
│       ├── S1-05_Pipeline_RAG.md          # Evidencia de integración del pipeline RAG
│       ├── S1-06_Evaluacion_QA.md         # Evidencia de pruebas unitarias y métricas
│       └── S1-07_Arquitectura_RAG.md      # Evidencia de arquitectura RAG consolidada
├── scripts/
│   └── ingestion/
│       └── ingest_knowledge.py            # Script de ingesta e indexación en Supabase pgvector
├── src/
│   ├── api/                               # Controladores y routers FastAPI
│   ├── app/                               # Frontend React 18 + Vite (SPA)
│   ├── database/                          # Conexión SQLAlchemy y modelos relacionales
│   ├── knowledge/
│   │   └── chunking/                      # Segmentador semántico clínico (ClinicalSemanticChunker)
│   ├── rag/
│   │   ├── embeddings/                    # Generador de embeddings con Hugging Face (384d)
│   │   ├── pipeline/                      # Pipeline RAG y ensamblador de contexto clínico
│   │   ├── retriever/                     # Recuperador semántico con filtrado por metadatos
│   │   └── vector_store/                  # Adaptador de pgvector en Supabase
│   └── services/                          # Lógica de servicios transaccionales
├── tests/
│   └── rag/
│       ├── test_chunking.py               # Tests unitarios del segmentador
│       ├── test_embeddings.py             # Tests unitarios del generador de embeddings
│       └── test_retrieval.py              # Tests unitarios del pipeline RAG
├── .env.example                           # Variables de entorno saneadas (placeholders)
├── Dockerfile                             # Contenedor Docker para despliegue en producción
├── README.md                              # Portada técnica y guía del repositorio
└── requirements.txt                       # Dependencias de Python
```

---

## 🎯 Matriz de Trazabilidad de Entregables (Sprint 1)

| Issue | Descripción del Entregable | Módulo / Ubicación en Repositorio | Estado |
| :---: | :--- | :--- | :---: |
| **`S1-01`** | **Base de Conocimiento y Ontología Médica:** Modelado de 10 patologías geriátricas, restricciones biomecánicas y reconocimiento al Ing. Julio Matute. | `data/knowledge_base/`<br/>`docs/knowledge/`<br/>[`issues/issues_sprint_1/S1-01_Base_Conocimiento.md`](issues/issues_sprint_1/S1-01_Base_Conocimiento.md) | ✅ **100%** (Aprobado) |
| **`S1-02`** | **Estrategia de Segmentación Lógica (Chunking):** Chunking semántico tripartito (`_DESC`, `_REC`, `_CONTRA`) preservando niveles de progresión segura (1-4). | `src/knowledge/chunking/chunker.py`<br/>`docs/rag/chunking-strategy.md`<br/>[`issues/issues_sprint_1/S1-02_Estrategia_Chunking.md`](issues/issues_sprint_1/S1-02_Estrategia_Chunking.md) | ✅ **100%** (Aprobado) |
| **`S1-03`** | **Generación de Representaciones Vectoriales (Embeddings):** Vectorización densa (384d) vía Hugging Face real y aserción estricta (`HUGGINGFACE_REAL_MODEL`). | `src/rag/embeddings/hf_embeddings.py`<br/>`docs/rag/embeddings-strategy.md`<br/>[`issues/issues_sprint_1/S1-03_Embeddings.md`](issues/issues_sprint_1/S1-03_Embeddings.md) | ✅ **100%** (Corregido y Verificado) |
| **`S1-04`** | **Base de Datos Vectorial con pgvector:** Almacenamiento en Supabase PostgreSQL con índice `HNSW` y similitud de coseno. | `src/rag/vector_store/pgvector_store.py`<br/>`docs/rag/vector-database.md`<br/>[`issues/issues_sprint_1/S1-04_Base_Vectorial_pgvector.md`](issues/issues_sprint_1/S1-04_Base_Vectorial_pgvector.md) | ✅ **100%** (Aprobado) |
| **`S1-05`** | **Pipeline RAG Integrado:** Orquestación de consulta, recuperación semántica y prompt clínico aumentado con telemetría unívoca y prueba automatizada mockeada. | `src/rag/pipeline/rag_pipeline.py`<br/>`src/rag/retriever/retriever.py`<br/>[`issues/issues_sprint_1/S1-05_Pipeline_RAG.md`](issues/issues_sprint_1/S1-05_Pipeline_RAG.md) | ✅ **100%** (Corregido y Verificado) |
| **`S1-06`** | **Evaluación Cuantitativa y QA:** Suite de tests automatizados, métricas de recuperación recalculadas (Hit Rate 100%, MRR 0.9000, P@3 0.6333) y telemetría de latencias. | `tests/rag/`<br/>`docs/evaluation/retrieval-metrics.md`<br/>[`issues/issues_sprint_1/S1-06_Evaluacion_QA.md`](issues/issues_sprint_1/S1-06_Evaluacion_QA.md) | ✅ **100%** (Corregido y Verificado) |
| **`S1-07`** | **Arquitectura RAG Consolidada:** Documentación arquitectónica consolidada, distinción formal de telemetría y purga terminológica metodológica. | `docs/architecture/rag-architecture.md`<br/>`docs/reports/sprint-1-report.md`<br/>[`issues/issues_sprint_1/S1-07_Arquitectura_RAG.md`](issues/issues_sprint_1/S1-07_Arquitectura_RAG.md) | ✅ **100%** (Corregido y Consolidado) |

---

## 🎯 Matriz de Trazabilidad de Entregables (Sprint 2: Agentes Inteligentes)

| Issue | Descripción del Entregable | Módulo / Ubicación en Repositorio | Estado |
| :---: | :--- | :--- | :---: |
| **`S2-01`** | **Refactorización y Evolución del Wellness Coach hacia Agente Inteligente:** Migración desde agente estático a arquitectura ReAct orientada a objetos en `src/`. | `src/agents/wellness/coach.py`<br/>[`issues/issues_sprint_2/S2-01_Refactorizacion_Wellness_Agent.md`](issues/issues_sprint_2/S2-01_Refactorizacion_Wellness_Agent.md) | ✅ **100%** (Completado) |
| **`S2-02`** | **Diseño y Herencia del Wellness Coach 2.0:** Herencia formal de `WellnessAgent`, orquestación de herramientas y depuración de llamadas residuales legacy. | `src/agents/wellness/coach.py`<br/>`src/agents/wellness/agent.py`<br/>[`issues/issues_sprint_2/S2-02_Diseno_Wellness_Coach_2.0.md`](issues/issues_sprint_2/S2-02_Diseno_Wellness_Coach_2.0.md) | ✅ **100%** (Completado) |
| **`S2-03`** | **Memoria Conversacional Persistente:** Persistencia de mensajes, turnos e interacciones en Supabase PostgreSQL con `PostgresMemoryStore`, eliminando estado volátil en RAM. | `src/memory/postgres_store.py`<br/>[`issues/issues_sprint_2/S2-03_Memoria_Conversacional.md`](issues/issues_sprint_2/S2-03_Memoria_Conversacional.md) | ✅ **100%** (Completado) |
| **`S2-04`** | **Tool Calling Dinámico e Integración:** Catálogo de 4 herramientas especializadas (`SafetyCheckTool`, `ExerciseCatalogTool`, `RAGSearchTool`, `LogHabitTool`) invocadas autónomamente. | `src/tools/wellness/`<br/>[`issues/issues_sprint_2/S2-04_Tool_Calling_Integracion.md`](issues/issues_sprint_2/S2-04_Tool_Calling_Integracion.md) | ✅ **100%** (Completado) |
| **`S2-05`** | **Patrón de Razonamiento ReAct:** Motor iterativo Thought → Action → Observation → Final Answer con guardrails de seguridad y control de ciclos. | `src/agents/wellness/reasoning.py`<br/>[`issues/issues_sprint_2/S2-05_Patron_ReAct.md`](issues/issues_sprint_2/S2-05_Patron_ReAct.md) | ✅ **100%** (Completado) |
| **`S2-06`** | **Evaluación Cuantitativa y Benchmark del Agente:** Suite completa de 20 escenarios clínicos con 100.0% Safety Compliance, 97.0% Tool Accuracy y 100.0% ReAct Validity. | `scripts/evaluation/evaluate_coach.py`<br/>`data/evaluation/coach_results/metrics_summary.json`<br/>[`issues/issues_sprint_2/S2-06_Evaluacion_Agente.md`](issues/issues_sprint_2/S2-06_Evaluacion_Agente.md) | ✅ **100%** (Completado) |
| **`S2-07`** | **Arquitectura Integral y Unificación del Endpoint /chat:** Conexión de extremo a extremo en FastAPI (`/api/v1/chat`), validación de integración automatizada (`test_chat_endpoint.py`) y sincronización documental. | `src/api/chat.py`<br/>`tests/integration/test_chat_endpoint.py`<br/>[`issues/issues_sprint_2/S2-07_Arquitectura_Resultados.md`](issues/issues_sprint_2/S2-07_Arquitectura_Resultados.md) | ✅ **100%** (Completado) |

---


## Instalación y ejecución (Guía de Reproducibilidad)

Sigue estos pasos para clonar, ejecutar la ingesta y validar las pruebas unitarias del sistema RAG localmente:

### 1. Clonar el repositorio y posicionarse en la rama del sprint
```bash
git clone https://github.com/YaskCode-laboratory/wellness-platform-team5.git
cd wellness-platform-team5
git checkout sprint-1
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

### 4. Ejecutar la ingesta y vectorización del conocimiento
```bash
python scripts/ingestion/ingest_knowledge.py
```
*Salida esperada:*
```text
[SeniorVital] Iniciando pipeline de ingesta clinica...
[Chunking] Chunks generados exitosamente: 30 fragmentos clinicos estructurados.
[Embeddings] Generando representaciones vectoriales (384d) para 30 documentos...
[VectorStore] Tabla 'clinical_knowledge_vectors' e indice HNSW inicializados en Supabase pgvector.
[SUCCESS] Ingesta e indexacion vectorial completada con exito.
```

### 5. Ejecutar la suite completa de pruebas automatizadas (RAG, Agente e Integración)
```bash
python -m pytest tests/rag/ tests/agents/ tests/integration/ -v
```
*Salida esperada:*
```text
tests/rag/test_chunking.py::test_semantic_chunker_generates_three_chunks_per_pathology PASSED
tests/rag/test_embeddings.py::test_embeddings_generator_returns_384_dimension_vector PASSED
tests/rag/test_retrieval.py::test_rag_pipeline_system_prompt_structure PASSED
tests/rag/test_retrieval.py::test_rag_pipeline_full_orchestration_with_telemetry PASSED
tests/agents/test_wellness_agent.py::... PASSED
tests/integration/test_chat_endpoint.py::test_chat_endpoint_react_cycle_with_tools_and_memory PASSED
tests/integration/test_chat_endpoint.py::test_chat_endpoint_direct_response_without_tools PASSED
tests/integration/test_chat_endpoint.py::test_chat_endpoint_guardrail_activation PASSED

============================== 10 passed in 3.12s ==============================
```

### 6. Ejecución de la API Backend y Frontend
```bash
# Iniciar Servidor FastAPI
uvicorn src.api.main:app --reload --port 8000
# Swagger UI disponible en: http://localhost:8000/docs

# Iniciar Frontend (en otra terminal)
cd src/app
npm install
npm run dev
# Aplicación web disponible en: http://localhost:5173
```

---

## 📑 Índice de Documentación Viva

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

### Sprint 2: Agentes Inteligentes, ReAct y Tool Calling
* 🤖 **Arquitectura del Wellness Coach Agent:** [`docs/agents/wellness-agent.md`](docs/agents/wellness-agent.md)
* 📊 **Evaluación Cuantitativa y Benchmark (20 Escenarios):** [`data/evaluation/coach_results/metrics_summary.json`](data/evaluation/coach_results/metrics_summary.json)
* 📋 **Informe Ejecutivo Sprint 2:** [`docs/reports/sprint-2-report.md`](docs/reports/sprint-2-report.md)
* 📂 **Evidencias de Issues (S2-01 a S2-07):** [`issues/issues_sprint_2/`](issues/issues_sprint_2/)

---

## Equipo

* **Daniel Alejandro Sánchez Ávila** — *Investigador y Desarrollador Backend / DevOps*
* **Abdénago Nahmens** — *Investigador y Desarrollador Frontend / UX-UI*
* **Dra. Yaskelly Yedra** — *Tutor Académico y Docente Titular de la Asignatura*
* **Ing. Julio Matute** — *Asesor Técnico-Clínico Gerontológico*

---

## Estado del proyecto

* **Fase Actual:** **Sprint 2: Agentes Inteligentes, ReAct y Tool Calling (Completado al 100% / 30% del Proyecto Total).**
* **Hitos Alcanzados:**
  - Base de conocimiento de 10 patologías geriátricas y RAG integrado (Sprint 1).
  - `WellnessCoachAgent` con herencia formal de `WellnessAgent` y arquitectura modular en `src/`.
  - Conexión de `PostgresMemoryStore` sobre Supabase PostgreSQL por sesión de usuario.
  - Motor de razonamiento ReAct (`reasoning.py`) con Tool Calling dinámico de 4 herramientas clínicas.
  - Endpoint `/api/v1/chat` integrado de extremo a extremo con telemetría estructurada.
  - Benchmark sobre 20 escenarios clínicos con 100.0% Safety Compliance, 97.0% Tool Accuracy y 100.0% ReAct Validity.
* **Próxima Fase:** **Sprint 3: Monitoreo, Tracking y Evaluación Preventiva Continua.**

