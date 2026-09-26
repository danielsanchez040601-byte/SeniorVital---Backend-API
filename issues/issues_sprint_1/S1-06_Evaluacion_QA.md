# 🧪 Issue S1-06: Evaluación Cuantitativa y QA del Sistema RAG

> **Materia:** Sistemas Inteligentes — Dra. Yaskelly Yedra  
> **Autores:** Daniel Alejandro Sánchez Ávila & Abdénago Nahmens (Team 5)  
> **Proyecto:** SeniorVital 2.0 — Plataforma Inteligente Wellness (+60)  
> **Sprint Técnico:** Sprint 1 — Ingeniería del Conocimiento y Sistemas RAG  
> **Estado:** Corregido y verificado con benchmark recalculado  

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

============================== 4 passed in 3.41s ==============================
```

---

## 🛠️ 2. Corrección del Criterio de Relevancia (Septiembre 2026)

Durante la revisión técnica del benchmark de recuperación, se detectó una heurística permisiva en la evaluación algorítmica:
```python
# Criterio anterior con sesgo permisivo
is_relevant = cid in expected or cid.startswith(cond)
```
Dado que cada patología contiene 3 fragmentos documentales (`_DESC`, `_REC`, `_CONTRA`), la condición `cid.startswith(cond)` marcaba como relevante cualquier fragmento perteneciente a la misma condición médica, incluso cuando la consulta solicitaba una contraindicación y el recuperador traía una prescripción. Esto causaba un sesgo sistemático que inflaba artificialmente la métrica `Precision@3` al valor ideal de 1.0000.

La condición fue refactorizada en `scripts/evaluation/evaluate_rag.py` para contrastar únicamente contra los identificadores exactos definidos en la verdad fundamental:
```python
# Criterio estricto corregido
is_relevant = cid in expected_chunk_ids
```

Asimismo, se desagregó la medición de latencias para distinguir el desempeño intrínseco del almacén vectorial frente al costo computacional de la inferencia densa en `retrieve_with_telemetry`:
1. **Latencia del Vector Store:** Tiempo exclusivo de la búsqueda por producto punto/similitud de coseno en memoria o base de datos.
2. **Latencia Total de Inferencia/Recuperación:** Ciclo completo que engloba la tokenización, inferencia en Hugging Face (`all-MiniLM-L6-v2`), búsqueda por similitud, filtrado de umbral y ensamblaje de la telemetría.

---

## 📊 3. Matriz de Métricas Cuantitativas Empíricas ($K = 3$)
Calculadas mediante `python scripts/evaluation/evaluate_rag.py` sobre `data/evaluation/rag_eval_dataset.json` tras la eliminación del sesgo de prefijo:

### Bloque A: Métricas de Recuperación Semántica (Retrieval Quality)
| Métrica de Recuperación | Valor Obtenido | Meta Exigida | Estado | Formulación y Observación Técnica |
| :--- | :---: | :---: | :---: | :--- |
| **Hit Rate @ 3 (Tasa de Acierto)** | **100.0%** | $\ge 85.0\%$ | ✅ **SUPERADA** | $\text{Hit@3} = 1.0$. Todas las consultas recuperaron al menos un fragmento relevante anotado dentro del Top-3. |
| **Mean Reciprocal Rank (MRR)** | **0.9000** | $\ge 0.80$ | ✅ **SUPERADA** | En 8 de 10 consultas el fragmento esperado ocupó la posición 1 ($\text{RR}=1.0$), mientras que en 2 consultas (`EPOC-06` y `PARK-07`) se ubicó en posición 2 ($\text{RR}=0.5$). |
| **Precision @ 3 (Verdad Fundamental)** | **0.6333** | $\ge 0.70$ | 📊 **0.6333** | Dado que el dataset modela 2 fragmentos esperados por consulta ($|\text{Expected}|=2$), el límite superior matemático para $K=3$ es $2/3 \approx 0.6667$. Un resultado de $0.6333$ refleja que 9 de 10 casos obtuvieron la máxima precisión teórica posible. |
| **Latencia Motor Vectorial (In-Memory)** | **3.18 ms** (P95: 4.11 ms) | $\le 20\text{ ms}$ | ✅ **ÓPTIMO** | Búsqueda coseno sobre los 30 fragmentos indexados en memoria. |
| **Latencia Total Recuperación (`retrieve_with_telemetry`)** | **421.20 ms** (P95: 559.93 ms) | $\le 1200\text{ ms}$ | ✅ **CUMPLIDA** | Inferencia densa con modelo real Hugging Face + búsqueda vectorial + telemetría post-ejecución. |

### Bloque B: Análisis de Evaluación de Generación (Response Evaluation)
| Métrica de Generación | Valor Obtenido | Meta Exigida | Tipo de Métrica | Estado |
| :--- | :---: | :---: | :--- | :---: |
| **Tasa de Adherencia Clínica** | **100.0%** | $\ge 90.0\%$ | **Heurística basada en reglas y palabras clave** | ✅ **CUMPLIDA** |

> **Nota Metodológica Obligatoria:**  
> `clinical_adherence_rate` se documenta estrictamente como una **métrica heurística basada en reglas y coincidencia de palabras clave clínicas** (`prohibid`, `advertencia`, `evitar`, `riesgo`, `recomenda`, `fuerza`). No se emplea como afirmación de "cero alucinaciones" ni como sustituto de métricas formales de *faithfulness* o *groundedness*.

---

## 🔬 4. Detalle de Consultas Anotadas y Resultados

```text
ID    | Condicion  | Hit@3   | MRR    | P@3    | Lat. Vec   | Lat. Total  | Top-1 Chunk Recuperado
--------------------------------------------------------------------------------------------
Q01   | OA-01      | SI      | 1.00   | 0.67   | 2.87 ms    | 207.50 ms   | OA-01_CONTRA
Q02   | SAR-02     | SI      | 1.00   | 0.67   | 3.72 ms    | 273.30 ms   | SAR-02_REC
Q03   | OST-03     | SI      | 1.00   | 0.67   | 2.54 ms    | 326.65 ms   | OST-03_REC
Q04   | ICC-04     | SI      | 1.00   | 0.67   | 3.35 ms    | 417.61 ms   | ICC-04_CONTRA
Q05   | DMT2-05    | SI      | 1.00   | 0.67   | 3.35 ms    | 424.81 ms   | DMT2-05_CONTRA
Q06   | EPOC-06    | SI      | 0.50   | 0.33   | 2.90 ms    | 559.93 ms   | EPOC-06_DESC
Q07   | PARK-07    | SI      | 0.50   | 0.67   | 1.94 ms    | 470.86 ms   | PARK-07_CONTRA
Q08   | ACV-08     | SI      | 1.00   | 0.67   | 3.00 ms    | 519.14 ms   | ACV-08_REC
Q09   | LUMB-09    | SI      | 1.00   | 0.67   | 4.11 ms    | 524.06 ms   | LUMB-09_CONTRA
Q10   | FRAG-10    | SI      | 1.00   | 0.67   | 4.02 ms    | 488.12 ms   | FRAG-10_REC
```

* **Telemetría Post-Ejecución Registrada en Reporte:** `embedding_mode: HUGGINGFACE_REAL_MODEL`, `vector_backend: IN_MEMORY_FALLBACK`, `llm_provider: deterministic_fallback`.
* **Cumplimiento Heurístico de Generación:** 10 de 10 casos cumplieron los criterios de adherencia clínica definidos en la evaluación.

---
**Archivos Asociados:**
- `data/evaluation/rag_eval_dataset.json`
- `scripts/evaluation/evaluate_rag.py`
- `docs/evaluation/retrieval-metrics.md`
- `data/evaluation/retrieval_benchmark_results.json`
- `docs/evaluation/retrieval_benchmark_results.json`
- `tests/rag/`
