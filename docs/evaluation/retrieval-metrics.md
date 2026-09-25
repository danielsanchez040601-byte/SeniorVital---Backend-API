# 📈 Métricas de Evaluación del Sistema RAG — SeniorVital 2.0

> **Materia:** Sistemas Inteligentes — Dra. Yaskelly Yedra  
> **Autores:** Daniel Sánchez & Abdénago Nahmens (Team 5) | **Asesoría Clínica:** Ing. Julio Matute  
> **Dataset de Evaluación:** `data/evaluation/rag_eval_dataset.json` (10 Consultas Clínicas Anotadas)  
> **Script de Evaluación:** `scripts/evaluation/evaluate_rag.py`  

---

## 🎯 1. Métricas de Evaluación Cuantitativa del Sistema RAG ($K = 3$)

Las métricas fueron calculadas matemáticamente de manera automatizada ejecutando el script `scripts/evaluation/evaluate_rag.py` sobre el dataset de benchmarking (`data/evaluation/rag_eval_dataset.json`), evaluando la relevancia exclusivamente contra los identificadores exactos de la verdad fundamental (`expected_chunk_ids`):

### Bloque A: Métricas de Recuperación Semántica (Retrieval Quality)

| Métrica de Recuperación | Valor Obtenido | Meta Exigida | Estado | Formulación Matemática y Análisis |
| :--- | :---: | :---: | :---: | :--- |
| **Hit Rate @ 3 (Tasa de Acierto)** | **100.0%** | $\ge 85.0\%$ | ✅ **SUPERADA** | $\text{Hit@K} = \frac{1}{|Q|} \sum_{q=1}^{|Q|} \mathbb{I}(\text{Top-}K_q \cap \text{Expected}_q \neq \emptyset)$. Todas las consultas recuperaron al menos un fragmento esperado en el Top-3. |
| **Mean Reciprocal Rank (MRR)** | **0.9000** | $\ge 0.80$ | ✅ **SUPERADA** | $\text{MRR} = \frac{1}{|Q|} \sum_{q=1}^{|Q|} \frac{1}{\text{rank}_q}$. En 8 de 10 casos el primer fragmento recuperado correspondió a la verdad fundamental; en 2 casos se ubicó en el rango 2 ($\text{RR}=0.50$). |
| **Precision @ 3 (Verdad Fundamental)** | **0.6333** | $\ge 0.70$ | 📊 **0.6333 (Techo: 0.6667)** | $\text{P@K} = \frac{|\text{Relevantes en Top-}K|}{K}$. Al fijar $K=3$ frente a pares anotados ($|\text{Expected}|=2$), el límite superior analítico es $2/3 \approx 0.6667$. Un valor empírico de $0.6333$ representa el $95.0\%$ del rendimiento teórico posible. |
| **Latencia Motor Vectorial (In-Memory)** | **3.18 ms** (P95: 4.11 ms) | $\le 20\text{ ms}$ | ✅ **ÓPTIMO** | Tiempo exclusivo de la consulta vectorial (búsqueda por similitud de coseno en espacio euclídeo / memoria). |
| **Latencia Total Recuperación (`retrieve_with_telemetry`)** | **421.20 ms** (P95: 559.93 ms) | $\le 1200\text{ ms}$ | ✅ **CUMPLIDA** | Tiempo completo de ejecución: generación densa de embeddings con modelo Hugging Face real, búsqueda vectorial, filtrado y telemetría. |

> ### 📌 Nota sobre el Criterio Estricto de Relevancia:
> La versión previa utilizaba la condición `cid in expected or cid.startswith(cond)`, provocando que cualquier fragmento de la misma patología contara como relevante e inflando artificialmente la precisión a 1.0000. Al eliminar la regla por prefijo y restringir la evaluación a `cid in expected_chunk_ids`, la métrica refleja la capacidad selectiva real del recuperador respecto a la necesidad clínica específica (prescripción vs. contraindicación).

---

### Bloque B: Análisis de Evaluación de Generación (Response Evaluation)

| Métrica de Generación | Valor Obtenido | Meta Exigida | Tipo de Métrica | Estado |
| :--- | :---: | :---: | :--- | :---: |
| **Tasa de Adherencia Clínica** | **100.0%** | $\ge 90.0\%$ | **Heurística basada en reglas y palabras clave** | ✅ **CUMPLIDA** |

> ### ⚠️ Delimitación Metodológica:
> * **Naturaleza Heurística:** La métrica `clinical_adherence_rate` inspecciona la presencia obligatoria de vocabulario restrictivo de seguridad (`prohibid`, `advertencia`, `evitar`, `riesgo`, `precaucion`, `contraindic`) en escenarios de contraindicación y vocabulario prescriptivo dosificado (`recomenda`, `fuerza`, `adaptad`, `guia`, `evidencia`) en rutinas.
> * **Delimitación de Alcance:** Esta verificación sintáctico-clínica no sustituye métricas de fidelidad semántica (*faithfulness*) o fundamentación (*groundedness*) mediante juicio médico ciego o evaluadores LLM-as-a-judge independientes.

---

## 📊 2. Desglose Detallado por Consulta de Evaluación

### Detalle de Recuperación (Bloque A):

| ID | Condición Evaluada | Hit@3 | MRR | Precision@3 | Lat. Vectorial | Lat. Total Recup. | Top-1 Chunk Recuperado |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Q01** | `OA-01` (Osteoartritis) | **SI** | 1.00 | 0.67 | 2.87 ms | 207.50 ms | `OA-01_CONTRA` |
| **Q02** | `SAR-02` (Sarcopenia / Fuerza) | **SI** | 1.00 | 0.67 | 3.72 ms | 273.30 ms | `SAR-02_REC` |
| **Q03** | `OST-03` (Osteoporosis / Fracturas) | **SI** | 1.00 | 0.67 | 2.54 ms | 326.65 ms | `OST-03_REC` |
| **Q04** | `ICC-04` (Insuficiencia Cardíaca) | **SI** | 1.00 | 0.67 | 3.35 ms | 417.61 ms | `ICC-04_CONTRA` |
| **Q05** | `DMT2-05` (Diabetes Mellitus 2) | **SI** | 1.00 | 0.67 | 3.35 ms | 424.81 ms | `DMT2-05_CONTRA` |
| **Q06** | `EPOC-06` (EPOC / Respiratorio) | **SI** | 0.50 | 0.33 | 2.90 ms | 559.93 ms | `EPOC-06_DESC` |
| **Q07** | `PARK-07` (Parkinson / Marcha) | **SI** | 0.50 | 0.67 | 1.94 ms | 470.86 ms | `PARK-07_CONTRA` |
| **Q08** | `ACV-08` (Accidente Cerebrovascular) | **SI** | 1.00 | 0.67 | 3.00 ms | 519.14 ms | `ACV-08_REC` |
| **Q09** | `LUMB-09` (Lumbalgia Mecánica) | **SI** | 1.00 | 0.67 | 4.11 ms | 524.06 ms | `LUMB-09_CONTRA` |
| **Q10** | `FRAG-10` (Fragilidad Geriátrica) | **SI** | 1.00 | 0.67 | 4.02 ms | 488.12 ms | `FRAG-10_REC` |

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
