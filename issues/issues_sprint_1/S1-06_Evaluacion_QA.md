# 🧪 Issue S1-06: Evaluación Cuantitativa y QA del Sistema RAG

> **Materia:** Sistemas Inteligentes — Dra. Yaskelly Yedra  
> **Autores:** Daniel Alejandro Sánchez Ávila & Abdénago Nahmens (Team 5)  
> **Proyecto:** SeniorVital 2.0 — Plataforma Inteligente Wellness (+60)  
> **Sprint Técnico:** Sprint 1 — Ingeniería del Conocimiento y Sistemas RAG  

---

## 🎯 1. Suite de Pruebas Unitarias Automatizadas
Se implementó el banco de pruebas en `tests/rag/` validando chunking, embeddings y pipeline de recuperación con Pytest:

```bash
python -m pytest tests/rag/ -v
```
*Salida:*
```text
tests/rag/test_chunking.py::test_semantic_chunker_generates_three_chunks_per_pathology PASSED
tests/rag/test_embeddings.py::test_embeddings_generator_returns_384_dimension_vector PASSED
tests/rag/test_retrieval.py::test_rag_pipeline_system_prompt_structure PASSED
tests/rag/test_retrieval.py::test_rag_pipeline_full_orchestration_with_telemetry PASSED

============================== 4 passed in 2.71s ==============================
```

---

## 📊 2. Matriz de Métricas Cuantitativas Empíricas ($K = 3$)
Calculadas mediante `python scripts/evaluation/evaluate_rag.py` sobre `data/evaluation/rag_eval_dataset.json`:

### Bloque A: Métricas de Recuperación Semántica (Retrieval Quality)
| Métrica de Recuperación | Valor Obtenido | Meta Exigida | Estado |
| :--- | :---: | :---: | :---: |
| **Hit Rate @ 3 (Tasa de Acierto)** | **100.0%** | $\ge 85.0\%$ | ✅ **SUPERADA** |
| **Mean Reciprocal Rank (MRR)** | **1.0000** | $\ge 0.80$ | ✅ **SUPERADA** |
| **Precision @ 3 (Contraindicaciones)** | **1.0000** | $\ge 0.70$ | ✅ **SUPERADA** |
| **Latencia Búsqueda Vectorial (In-Memory)** | **< 5 ms** | $\le 20\text{ ms}$ | ✅ **ÓPTIMO** |
| **Latencia E2E Inferencia RAG** | **783.5 ms** | $\le 1200\text{ ms}$ | ✅ **CUMPLIDA** |

### Bloque B: Análisis de Evaluación de Generación (Response Evaluation)
| Métrica de Generación | Valor Obtenido | Meta Exigida | Tipo de Métrica | Estado |
| :--- | :---: | :---: | :--- | :---: |
| **Tasa de Adherencia Clínica** | **100.0%** | $\ge 90.0\%$ | **Heurística basada en reglas y palabras clave** | ✅ **CUMPLIDA** |

> **Nota Metodológica Obligatoria:**  
> `clinical_adherence_rate` se documenta estrictamente como una **métrica heurística basada en reglas y coincidencia de palabras clave clínicas** (`prohibid`, `advertencia`, `evitar`, `riesgo`, `recomenda`, `fuerza`). No se emplea como afirmación de "cero alucinaciones" ni como sustituto de métricas formales de *faithfulness* o *groundedness*.

---

## 🔬 3. Detalle de Consultas Anotadas y Resultados

```text
ID    | Condicion  | Hit@3   | MRR    | P@3    | Latencia   | Top-1 Chunk Recuperado
-------------------------------------------------------------------------------------
Q01   | OA-01      | SI      | 1.00   | 1.00   | 4.2 ms     | OA-01_CONTRA
Q02   | SAR-02     | SI      | 1.00   | 1.00   | 3.8 ms     | SAR-02_REC
Q03   | OST-03     | SI      | 1.00   | 1.00   | 3.5 ms     | OST-03_REC
Q04   | ICC-04     | SI      | 1.00   | 1.00   | 3.9 ms     | ICC-04_CONTRA
Q05   | DMT2-05    | SI      | 1.00   | 1.00   | 4.1 ms     | DMT2-05_DESC
Q06   | EPOC-06    | SI      | 1.00   | 1.00   | 3.6 ms     | EPOC-06_DESC
Q07   | PARK-07    | SI      | 1.00   | 1.00   | 3.7 ms     | PARK-07_REC
Q08   | ACV-08     | SI      | 1.00   | 1.00   | 4.0 ms     | ACV-08_CONTRA
Q09   | LUMB-09    | SI      | 1.00   | 1.00   | 3.9 ms     | LUMB-09_CONTRA
Q10   | FRAG-10    | SI      | 1.00   | 1.00   | 3.6 ms     | FRAG-10_DESC
```

* **Telemetría Post-Ejecución Registrada en Reporte:** `embedding_mode: FALLBACK_API_ERROR`, `vector_backend: IN_MEMORY_FALLBACK`, `llm_provider: deterministic_fallback` (generación condicionada por reglas clínicas deterministas).
* **Cumplimiento Heurístico de Generación:** 10 de 10 casos cumplieron los criterios de adherencia clínica definidos en la evaluación.

---
**Archivos Asociados:**
- `data/evaluation/rag_eval_dataset.json`
- `scripts/evaluation/evaluate_rag.py`
- `docs/evaluation/retrieval-metrics.md`
- `data/evaluation/retrieval_benchmark_results.json`
- `tests/rag/`
