# ✂️ Estrategia de Segmentación Semántica (Chunking)

> **Materia:** Sistemas Inteligentes — Dra. Yaskelly Yedra  
> **Autores:** Daniel Sánchez & Abdenago Nahmens | **Asesoría Clínica:** Ing. Julio Matute  

---

## 1. Justificación de la Estrategia
En el dominio gerontológico, mezclar descripciones generales con contraindicaciones críticas en un solo fragmento masivo degrada la precisión semántica y aumenta el riesgo de alucinaciones en el LLM.

Se implementó una estrategia de **Chunking Semántico Estructurado Tripartito**:
1. **Chunk de Perfil Clínico (`_DESC`):** 200-300 tokens con definición médica y limitaciones funcionales.
2. **Chunk de Prescripción (`_REC`):** 150-250 tokens con modalidades recomendadas y niveles seguros (1-4).
3. **Chunk de Contraindicaciones (`_CONTRA`):** 100-200 tokens con filtros duros y movimientos prohibidos.

## 2. Metadatos Inyectados
Cada fragmento contiene:
* `pathology_id` (e.g. `OA-01`)
* `category` (e.g. `Musculoesquelética`)
* `chunk_type` (`clinical_profile`, `recommended_exercises`, `contraindications`)
* `max_safe_level` (Límite superior de progresión)
