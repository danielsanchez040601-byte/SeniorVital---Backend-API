# 📋 Informe Técnico Ejecutivo — Sprint 1: Ingeniería del Conocimiento y RAG

> **Materia:** Sistemas Inteligentes — Dra. Yaskelly Yedra  
> **Autores:** Daniel Alejandro Sánchez Ávila & Abdénago Nahmens (Team 5)  
> **Asesoría Clínica:** Ing. Julio Matute  
> **Fecha de Consolidación:** Septiembre 2026 | **Ponderación:** 15% del Proyecto  

---

## 🎯 1. Resumen Ejecutivo
El **Sprint 1** consolidó los objetivos estipulados para la evolución de SeniorVital hacia un sistema inteligente asistido por IA, integrando una arquitectura RAG Open Source y Cloud-Native con persistencia vectorial en Supabase (`pgvector`), modelos LLM con tolerancia a fallos, guardrails clínicos y **Telemetría en Tiempo de Ejecución (Post-Execution Telemetry)**.

---

## 🏛️ 2. Distinción Formal de Arquitectura

Para responder de forma rigurosa a las observaciones de trazabilidad y reproducibilidad técnica, se establece la distinción explícita entre la arquitectura configurada contractualmente y la arquitectura efectivamente ejecutada durante los ciclos de prueba:

### A. Arquitectura Configurada (Capacidades Contractuales del Software)
* **Capa de Embeddings:** Modelo `sentence-transformers/all-MiniLM-L6-v2` (384 dimensiones) consumido mediante Hugging Face Inference API / Local, con normalización L2 unitaria y fallback determinista semántico proyectado en 384d.
* **Capa de Persistencia Vectorial:** Base de datos relacional y vectorial en Supabase PostgreSQL con extensión `pgvector`, tabla `clinical_knowledge_embeddings` e índice `HNSW` (`vector_cosine_ops`, $m=16$, $ef\_construction=64$). Soporta fallback transparente en memoria (`IN_MEMORY_FALLBACK`).
* **Capa de Generación Aumentada (LLM):** Cascada de tolerancia a fallos con 3 niveles:
  1. *Primario:* Google AI Studio (`gemini-flash-lite-latest`, `gemini-2.5-flash-lite`).
  2. *Secundario:* Pool gratuito en OpenRouter (`liquid/lfm-2.5-2.6b:free`, `nvidia/nemotron-3.5-lightning:free`, `meta-llama/llama-3.2-3b-instruct:free`).
  3. *Terciario (Offline / deterministic_fallback):* Motor de Razonamiento Clínico Determinista SeniorVital basado en evidencia recuperada de guías OARSI, EWGSOP2 y Vivifrail.
* **Guardrails de Seguridad:** Mecanismo Zero-Context Fallback que rechaza consultas fuera de dominio médico o con similitud $< 0.40$.

### B. Arquitectura Efectivamente Ejecutada (Telemetría de Pruebas Locales y CI)
En el entorno local y de integración continua (CI), el sistema registra con exactitud el mecanismo que produjo los resultados:
* **Modo de Embeddings:** `HUGGINGFACE_REAL_MODEL` (generación con modelo denso real en validación S1-03 y evaluación de recuperación) y `FALLBACK_CI` (en entornos aislados de CI).
* **Backend Vectorial:** `IN_MEMORY_FALLBACK` (búsqueda por similitud de coseno sobre los 30 chunks clínicos en memoria ante ausencia de sesión SQL remota).
* **Proveedor LLM:** `deterministic_fallback` (respuestas deterministas condicionadas estrictamente por la evidencia clínica recuperada).

---

## 📊 3. Matriz de Trazabilidad y Cumplimiento (S1-01 $\rightarrow$ S1-07)

| Issue | Entregable en `/src` | Documentación en `/docs` | Script / Prueba Automatizada | Métrica / Resultado Real | Estado |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **S1-01** | `data/knowledge_base/` | `docs/knowledge/` | `clinical_knowledge_base.json` | 10 condiciones clínicas modeladas con asesoría de Ing. Julio Matute | ✅ **100%** (Aprobado) |
| **S1-02** | `src/knowledge/chunking/` | `docs/rag/chunking-strategy.md` | `tests/rag/test_chunking.py` | 30 chunks estructurados (`_DESC`, `_REC`, `_CONTRA`) | ✅ **100%** (Aprobado) |
| **S1-03** | `src/rag/embeddings/` | `docs/rag/embeddings-strategy.md` | `scripts/evaluation/test_hf_embeddings.py` | Vector 384d, Norma L2 = 1.0000, inferencia real `HUGGINGFACE_REAL_MODEL` y aserción estricta superada | ✅ **100%** (Corregido y Verificado) |
| **S1-04** | `src/rag/vector_store/` | `docs/rag/vector-database.md` | `scripts/indexing/index_pgvector.py` | Reporte explícito de `backend_used` (pgvector / in-memory) | ✅ **100%** (Aprobado) |
| **S1-05** | `src/rag/pipeline/` | `docs/architecture/rag-architecture.md` | `tests/rag/test_retrieval.py` | Pipeline E2E con telemetría unívoca y test automatizado con mocks deterministas | ✅ **100%** (Corregido y Verificado) |
| **S1-06** | `data/evaluation/` | `docs/evaluation/retrieval-metrics.md` | `scripts/evaluation/evaluate_rag.py` | Hit Rate@3 = 100%, MRR = 0.9000, P@3 = 0.6333 (techo 0.6667), lat. vectorial = 3.18 ms | ✅ **100%** (Corregido y Verificado) |
| **S1-07** | Consolidación | `docs/reports/sprint-1-report.md` | `pytest tests/rag/ -v` | Consolidación arquitectónica, purga terminológica, rutas canónicas y 4/4 tests en verde | ✅ **100%** (Corregido y Consolidado) |

---

## 🔬 4. Métricas Empíricas de Evaluación RAG (Dataset de 10 Consultas)

Las métricas reflejan la combinación tecnológica concreta de la corrida de evaluación empírica (`evaluate_rag.py`) tras eliminar la regla por prefijo y evaluar exclusivamente contra los identificadores exactos de verdad fundamental:

### Bloque A: Calidad de Recuperación (Retrieval Quality)
* **Hit Rate @ 3:** **100.00%** (Meta: $\ge 85.0\%$) $\rightarrow$ **SUPERADA**
* **Mean Reciprocal Rank (MRR):** **0.9000** (Meta: $\ge 0.80$) $\rightarrow$ **SUPERADA**
* **Precision @ 3:** **0.6333** (Meta: $\ge 0.70$) $\rightarrow$ **0.6333** (Resultado consistente con la estructura del dataset anotado donde $|\text{Expected}|=2$; el techo teórico máximo es $2/3 \approx 0.6667$, habiendo alcanzado el $95\%$ de dicho límite).
* **Latencia del Motor Vectorial:** **3.18 ms** promedio (P95: 4.11 ms)
* **Latencia Total de Recuperación (`retrieve_with_telemetry`):** **421.20 ms** promedio (P95: 559.93 ms)
* **Combinación Tecnológica Efectiva:**
  * **Modo de Embeddings:** `HUGGINGFACE_REAL_MODEL`
  * **Backend Vectorial:** `IN_MEMORY_FALLBACK`

### Bloque B: Evaluación de Generación (Response Evaluation)
* **Tasa de Adherencia Clínica:** **100.00%** (Meta: $\ge 90.0\%$) $\rightarrow$ **SUPERADA** (Métrica heurística basada en reglas y coincidencia de palabras clave clínicas).
* **Proveedor LLM Efectivo:** `deterministic_fallback`
* **Consultas Evaluadas:** 10 de 10 casos cumplieron los criterios de adherencia clínica definidos en la evaluación (presencia de directrices de seguridad y dosificación sin extrapolaciones no fundamentadas).

---

## 🛰️ 5. Estructura de Telemetría Post-Ejecución Verificada

```json
{
  "query": "Tengo osteoartritis severa en rodilla, puedo hacer sentadillas con salto?",
  "status": "SUCCESS",
  "provider": "SeniorVital Clinical RAG Reasoning Engine",
  "telemetry": {
    "embedding_mode": "HUGGINGFACE_REAL_MODEL",
    "vector_backend": "IN_MEMORY_FALLBACK",
    "llm_provider": "deterministic_fallback",
    "vector_store_latency_ms": 3.18
  },
  "retrieved_chunks": [ ... ],
  "response": "[ADVERTENCIA CLINICA]: No es seguro realizar sentadillas con salto..."
}
```

---

## 🚀 6. Preparación para el Sprint 2
El pipeline RAG instrumentado y validado constituye la herramienta de recuperación (*Tool / Skill*) base que consumirá el **Wellness Agent** en el **Sprint 2: Agentes Inteligentes Modernos**, operando bajo el framework ReAct con trazabilidad integral de invocaciones.
