# 📈 Métricas de Evaluación del Sistema RAG — SeniorVital 2.0

> **Materia:** Sistemas Inteligentes — Dra. Yaskelly Yedra  
> **Autores:** Daniel Sánchez & Abdénago Nahmens (Team 5) | **Asesoría Clínica:** Ing. Julio Matute  
> **Dataset de Evaluación:** `data/evaluation/rag_eval_dataset.json` (10 Consultas Clínicas Anotadas)  
> **Script de Evaluación:** `scripts/evaluation/evaluate_rag.py`  

---

## 🎯 1. Resumen de Métricas Cuantitativas Empíricas ($K = 3$)

Las métricas fueron calculadas matemáticamente de manera automatizada ejecutando el script `scripts/evaluation/evaluate_rag.py` sobre el dataset de benchmarking:

| Métrica de Evaluación | Valor Obtenido | Meta Exigida | Estado |
| :--- | :---: | :---: | :---: |
| **Hit Rate @ 3 (Tasa de Acierto)** | **100.0%** | $\ge 85.0\%$ | ✅ **SUPERADA** |
| **Mean Reciprocal Rank (MRR)** | **1.0000** | $\ge 0.80$ | ✅ **SUPERADA** |
| **Precision @ 3 (Contraindicaciones)** | **1.0000** | $\ge 0.70$ | ✅ **SUPERADA** |
| **Tiempo de Búsqueda Vectorial (In-Memory)** | **< 5 ms** | $\le 20\text{ ms}$ | ✅ **ÓPTIMO** |
| **Latencia Total Inferencia RAG (E2E)** | **783.5 ms** | $\le 1200\text{ ms}$ | ✅ **CUMPLIDA** |

---

## 📊 2. Desglose Detallado por Consulta de Evaluación

| ID | Condición Evaluada | Hit@3 | MRR | Precision@3 | Top-1 Chunk Recuperado |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **Q01** | `OA-01` (Osteoartritis) | **SI** | 1.00 | 1.00 | `OA-01_CONTRA` |
| **Q02** | `SAR-02` (Sarcopenia / Fuerza) | **SI** | 1.00 | 1.00 | `SAR-02_REC` |
| **Q03** | `OST-03` (Osteoporosis / Fracturas) | **SI** | 1.00 | 1.00 | `OST-03_REC` |
| **Q04** | `ICC-04` (Insuficiencia Cardíaca) | **SI** | 1.00 | 1.00 | `ICC-04_CONTRA` |
| **Q05** | `DMT2-05` (Diabetes Mellitus 2) | **SI** | 1.00 | 1.00 | `DMT2-05_DESC` |
| **Q06** | `EPOC-06` (EPOC / Respiratorio) | **SI** | 1.00 | 1.00 | `EPOC-06_DESC` |
| **Q07** | `PARK-07` (Parkinson / Marcha) | **SI** | 1.00 | 1.00 | `PARK-07_REC` |
| **Q08** | `ACV-08` (Accidente Cerebrovascular) | **SI** | 1.00 | 1.00 | `ACV-08_CONTRA` |
| **Q09** | `LUMB-09` (Lumbalgia Mecánica) | **SI** | 1.00 | 1.00 | `LUMB-09_CONTRA` |
| **Q10** | `FRAG-10` (Fragilidad Geriátrica) | **SI** | 1.00 | 1.00 | `FRAG-10_DESC` |

---

## 🔬 3. Reproducibilidad
Para reproducir estos resultados empíricos en cualquier entorno local o runner de CI:
```bash
python scripts/evaluation/evaluate_rag.py
```
El reporte estructurado se guarda automáticamente en `docs/evaluation/retrieval_benchmark_results.json`.
