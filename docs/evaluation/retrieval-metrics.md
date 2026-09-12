# 📈 Métricas de Evaluación del Sistema RAG — SeniorVital 2.0

> **Materia:** Sistemas Inteligentes — Dra. Yaskelly Yedra  
> **Autores:** Daniel Sánchez & Abdénago Nahmens (Team 5) | **Asesoría Clínica:** Ing. Julio Matute  
> **Dataset de Evaluación:** `data/evaluation/rag_eval_dataset.json` (10 Consultas Clínicas Anotadas)  
> **Script de Evaluación:** `scripts/evaluation/evaluate_rag.py`  

---

## 🎯 1. Métricas de Evaluación Cuantitativa del Sistema RAG ($K = 3$)

Las métricas fueron calculadas matemáticamente de manera automatizada ejecutando el script `scripts/evaluation/evaluate_rag.py` sobre el dataset de benchmarking (`data/evaluation/rag_eval_dataset.json`):

### Bloque A: Métricas de Recuperación Semántica (Retrieval Quality)
Métricas formales de recuperación de información sobre los fragmentos documentales esperados:

| Métrica de Recuperación | Valor Obtenido | Meta Exigida | Estado | Formulación Matemática |
| :--- | :---: | :---: | :---: | :--- |
| **Hit Rate @ 3 (Tasa de Acierto)** | **100.0%** | $\ge 85.0\%$ | ✅ **SUPERADA** | $\text{Hit@K} = \frac{1}{|Q|} \sum_{q=1}^{|Q|} \mathbb{I}(\text{Top-}K_q \cap \text{Expected}_q \neq \emptyset)$ |
| **Mean Reciprocal Rank (MRR)** | **1.0000** | $\ge 0.80$ | ✅ **SUPERADA** | $\text{MRR} = \frac{1}{|Q|} \sum_{q=1}^{|Q|} \frac{1}{\text{rank}_q}$ |
| **Precision @ 3 (Contraindicaciones)** | **1.0000** | $\ge 0.70$ | ✅ **SUPERADA** | $\text{P@K} = \frac{|\text{Relevantes en Top-}K|}{K}$ |
| **Latencia Búsqueda Vectorial** | **< 5 ms** | $\le 20\text{ ms}$ | ✅ **ÓPTIMO** | Tiempo de ejecución de producto punto/distancia coseno |
| **Latencia Total Pipeline RAG** | **783.5 ms** | $\le 1200\text{ ms}$ | ✅ **CUMPLIDA** | Latencia E2E (recuperación + inferencia + telemetría) |

---

### Bloque B: Análisis de Evaluación de Generación (Response Evaluation)
Evaluación operacional de la respuesta generada por el modelo:

| Métrica de Generación | Valor Obtenido | Meta Exigida | Tipo de Métrica | Estado |
| :--- | :---: | :---: | :--- | :---: |
| **Tasa de Adherencia Clínica** | **100.0%** | $\ge 90.0\%$ | **Heurística basada en reglas y palabras clave** | ✅ **CUMPLIDA** |

> ### ⚠️ Precisión Metodológica y Delimitación Conceptual:
> * **Naturaleza Heurística:** La métrica `clinical_adherence_rate` es una **métrica heurística basada en reglas y coincidencia de palabras clave clínicas** (inspección de términos de seguridad como `prohibid`, `advertencia`, `evitar`, `riesgo`, `recomenda`, `fuerza`, `dosificacion`).
> * **Sin Afirmación de Cero Alucinaciones:** Esta métrica evalúa la presencia de directrices y restricciones léxicas en la respuesta, pero **no constituye por sí misma una prueba de fidelidad semántica estricta (*faithfulness*), fundamentación factual (*groundedness*) ni ausencia absoluta de alucinaciones**, aspectos que requieren procedimientos de evaluación independientes o paneles médicos de validación empírica.

---

## 📊 2. Desglose Detallado por Consulta de Evaluación

### Detalle de Recuperación (Bloque A):
| ID | Condición Evaluada | Hit@3 | MRR | Precision@3 | Latencia | Top-1 Chunk Recuperado |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **Q01** | `OA-01` (Osteoartritis) | **SI** | 1.00 | 1.00 | 4.2 ms | `OA-01_CONTRA` |
| **Q02** | `SAR-02` (Sarcopenia / Fuerza) | **SI** | 1.00 | 1.00 | 3.8 ms | `SAR-02_REC` |
| **Q03** | `OST-03` (Osteoporosis / Fracturas) | **SI** | 1.00 | 1.00 | 3.5 ms | `OST-03_REC` |
| **Q04** | `ICC-04` (Insuficiencia Cardíaca) | **SI** | 1.00 | 1.00 | 3.9 ms | `ICC-04_CONTRA` |
| **Q05** | `DMT2-05` (Diabetes Mellitus 2) | **SI** | 1.00 | 1.00 | 4.1 ms | `DMT2-05_DESC` |
| **Q06** | `EPOC-06` (EPOC / Respiratorio) | **SI** | 1.00 | 1.00 | 3.6 ms | `EPOC-06_DESC` |
| **Q07** | `PARK-07` (Parkinson / Marcha) | **SI** | 1.00 | 1.00 | 3.7 ms | `PARK-07_REC` |
| **Q08** | `ACV-08` (Accidente Cerebrovascular) | **SI** | 1.00 | 1.00 | 4.0 ms | `ACV-08_CONTRA` |
| **Q09** | `LUMB-09` (Lumbalgia Mecánica) | **SI** | 1.00 | 1.00 | 3.9 ms | `LUMB-09_CONTRA` |
| **Q10** | `FRAG-10` (Fragilidad Geriátrica) | **SI** | 1.00 | 1.00 | 3.6 ms | `FRAG-10_DESC` |

### Detalle de Adherencia Heurística de Generación (Bloque B):
* **Casos con Contraindicación:** 100% de las respuestas incorporaron términos restrictivos y advertencias de seguridad médica.
* **Casos de Prescripción:** 100% de las respuestas incorporaron directrices de dosificación y ejercicios adaptados.
* **Total de Casos Evaluados:** 10 de 10 casos cumplieron los criterios de adherencia clínica definidos en la evaluación.

---

## 🔬 3. Reproducibilidad y Reporte Automatizado
Para reproducir estos resultados empíricos en cualquier entorno local o runner de CI:
```bash
python scripts/evaluation/evaluate_rag.py
```
El reporte estructurado se guarda automáticamente en `data/evaluation/retrieval_benchmark_results.json` y `docs/evaluation/retrieval_benchmark_results.json`, registrando la telemetría post-ejecución efectiva (`embedding_mode`, `vector_backend`, `llm_provider`).
