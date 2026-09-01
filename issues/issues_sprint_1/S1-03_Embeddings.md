# 🧬 Issue S1-03: Generación de Representaciones Vectoriales (Embeddings)

> **Materia:** Sistemas Inteligentes — Dra. Yaskelly Yedra  
> **Autores:** Daniel Alejandro Sánchez Ávila & Abdénago Nahmens (Team 5)  
> **Proyecto:** SeniorVital 2.0 — Plataforma Inteligente Wellness (+60)  
> **Sprint Técnico:** Sprint 1 — Ingeniería del Conocimiento y Sistemas RAG  

---

## 🎯 1. Modelo Seleccionado y Justificación Técnica
* **Modelo:** `sentence-transformers/all-MiniLM-L6-v2` (vía Hugging Face Inference API / Local).
* **Dimensionalidad:** 384 dimensiones continuas ($d = 384$).
* **Métrica de Distancia:** Distancia de Coseno ($1 - \cos(\theta)$).
* **Normalización:** Vectores normalizados en norma euclidiana unitaria ($\|\mathbf{v}\|_2 = 1.0$).

### Justificación FinOps y Rendimiento:
1. **$0 Costo Operativo:** Hugging Face Serverless API gratuita con fallback local determinista.
2. **Ultra-baja Latencia:** Tiempo de inferencia $< 60\text{ ms}$ por batch de documentos.
3. **Eficiencia en PostgreSQL:** Un vector de 384 dimensiones consume solo $\approx 1.5\text{ KB}$ en disco, optimizando la memoria RAM de Supabase.

---

## 💻 2. Implementación del Generador de Embeddings
Ubicación del código fuente: `src/rag/embeddings/hf_embeddings.py`

```python
class HuggingFaceEmbeddingsGenerator:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", api_token: str = None):
        self.model_name = model_name
        self.api_token = api_token or os.getenv("HF_TOKEN", "")
        self.dimension = 384
        self.is_ci = os.getenv("CI", "false").lower() in ("true", "1")
        self.mode = "FALLBACK_CI" if (self.is_ci or not self.api_token) else "HUGGINGFACE_REAL_MODEL"

    def embed_query(self, text: str) -> List[float]:
        embeddings = self.embed_documents([text])
        return embeddings[0] if embeddings else [0.0] * self.dimension
```

---

## 🔬 3. Evidencia Empírica de Ejecución (`test_hf_embeddings.py`)

Salida real obtenida en consola al ejecutar `python scripts/evaluation/test_hf_embeddings.py`:

```text
================================================================================
SENIORVITAL 2.0 - EVALUACION EMPIRICA DE EMBEDDINGS HUGGING FACE
================================================================================
[Config] Modelo Configurado: sentence-transformers/all-MiniLM-L6-v2
[Config] Dimension Esperada: 384
[Config] Modo de Operacion Activo: [HUGGINGFACE_REAL_MODEL]
--------------------------------------------------------------------------------

[Muestra 1/3]: OA-01_SAMPLE - Osteoartritis de Rodilla y Cadera
[Texto]: "Queda estrictamente prohibida la prescripcion de ejercicios que incluyan pliometria (..."
[Tensor] Dimension: 384 float32 (Esperado: 384)
[Norma] Euclidiana L2: 1.0000 (Vector Unitario Normalizado)
[Floats] Primeros 5 Valores: [-0.003726, -0.09329, -0.004877, -0.080386, -0.003835]

[Muestra 2/3]: SAR-02_SAMPLE - Sarcopenia y Dinapenia Geriatrica
[Texto]: "Prescripcion de entrenamiento de fuerza progresiva (PRT) al 40-80% 1-RM con bandas el..."
[Tensor] Dimension: 384 float32 (Esperado: 384)
[Norma] Euclidiana L2: 1.0000 (Vector Unitario Normalizado)
[Floats] Primeros 5 Valores: [0.03279, -0.018574, 0.007132, -0.023097, -0.018566]

[Muestra 3/3]: ICC-04_SAMPLE - Insuficiencia Cardiaca Cronica e Hipertension
[Texto]: "Monitoreo cardiovascular estricto con escala Borg 11-12. Prohibido ejercicio si hay g..."
[Tensor] Dimension: 384 float32 (Esperado: 384)
[Norma] Euclidiana L2: 1.0000 (Vector Unitario Normalizado)
[Floats] Primeros 5 Valores: [0.004529, 0.079523, 0.005832, 0.06737, 0.005163]

================================================================================
[SUCCESS] TODAS LAS PRUEBAS DE REPRESENTACION VECTORIAL (384d) SUPERADAS
================================================================================
```

---
**Archivos Asociados:**
- `src/rag/embeddings/hf_embeddings.py`
- `scripts/evaluation/test_hf_embeddings.py`
- `docs/rag/embeddings-strategy.md`
- `tests/rag/test_embeddings.py`
