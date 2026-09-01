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

============================== 3 passed in 1.34s ==============================
```

---

## 📊 2. Matriz de Métricas Cuantitativas Empíricas ($K = 3$)
Calculadas mediante `python scripts/evaluation/evaluate_rag.py` sobre `data/evaluation/rag_eval_dataset.json`:

| Métrica de Evaluación | Valor Obtenido | Meta Exigida | Estado |
| :--- | :---: | :---: | :---: |
| **Hit Rate @ 3 (Tasa de Acierto)** | **100.0%** | $\ge 85.0\%$ | ✅ **SUPERADA** |
| **Mean Reciprocal Rank (MRR)** | **1.0000** | $\ge 0.80$ | ✅ **SUPERADA** |
| **Precision @ 3 (Contraindicaciones)** | **1.0000** | $\ge 0.70$ | ✅ **SUPERADA** |
| **Latencia Búsqueda Vectorial (In-Memory)** | **< 5 ms** | $\le 20\text{ ms}$ | ✅ **ÓPTIMO** |

---

## 🔬 3. Detalle de Consultas Anotadas y Resultados

```text
ID    | Condicion  | Hit@3   | MRR    | P@3    | Top-1 Chunk Recuperado
-------------------------------------------------------------------------------------
Q01   | OA-01      | SI      | 1.00   | 1.00   | OA-01_CONTRA
Q02   | SAR-02     | SI      | 1.00   | 1.00   | SAR-02_REC
Q03   | OST-03     | SI      | 1.00   | 1.00   | OST-03_REC
Q04   | ICC-04     | SI      | 1.00   | 1.00   | ICC-04_CONTRA
Q05   | DMT2-05    | SI      | 1.00   | 1.00   | DMT2-05_DESC
Q06   | EPOC-06    | SI      | 1.00   | 1.00   | EPOC-06_DESC
Q07   | PARK-07    | SI      | 1.00   | 1.00   | PARK-07_REC
Q08   | ACV-08     | SI      | 1.00   | 1.00   | ACV-08_CONTRA
Q09   | LUMB-09    | SI      | 1.00   | 1.00   | LUMB-09_CONTRA
Q10   | FRAG-10    | SI      | 1.00   | 1.00   | FRAG-10_DESC
```

---
**Archivos Asociados:**
- `data/evaluation/rag_eval_dataset.json`
- `scripts/evaluation/evaluate_rag.py`
- `docs/evaluation/retrieval-metrics.md`
- `tests/rag/`
