# 🧬 Estrategia de Representación Vectorial (Embeddings)

> **Materia:** Sistemas Inteligentes — Maestría en TIC (LUZ)  
> **Docente:** Dra. Yaskelly Yedra  
> **Autores:** Daniel Sánchez & Abdénago Nahmens  
> **Asesoría Clínica:** Ing. Julio Matute  
> **Entregable:** Sprint 1 — Issue S1-03  

---

## 1. Selección y Configuración del Modelo de Embeddings

Para transformar el conocimiento clínico gerontológico en representaciones vectoriales densas, se seleccionó el modelo **`sentence-transformers/all-MiniLM-L6-v2`** operado a través de la infraestructura serverless de **Hugging Face Inference API** y ejecutado localmente mediante inferencia neuronal.

### Ficha Técnica del Modelo:
* **Arquitectura:** MiniLM Transformer de 6 capas, 384 dimensiones ocultas y 12 cabezas de atención.
* **Dimensionalidad Vectorial ($d$):** **384 dimensiones continuas** (`float32`).
* **Función de Similitud / Métrica de Distancia:** Distancia y Similitud de Coseno ($\cos(\theta) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2}$).
* **Normalización Euclídea:** Normalización a norma unitaria ($\|\mathbf{v}\|_2 = 1.0000$), permitiendo que el producto punto equivalga directamente a la similitud coseno.
* **Justificación FinOps y Rendimiento:**
  - $0 costo por consulta (Hugging Face Serverless Inference).
  - Tiempo de inferencia inferior a $60\text{ ms}$ por fragmento.
  - Almacenamiento eficiente en PostgreSQL con extensión `pgvector` ($1.5\text{ KB}$ por registro indexado).

---

## 2. Diferenciación Formal de Entornos: Modelo Real vs Fallback de CI

En cumplimiento estricto con las directivas de evaluación de la Dra. Yaskelly Yedra, la implementación en [`src/rag/embeddings/hf_embeddings.py`](../../src/rag/embeddings/hf_embeddings.py) separa de forma explícita el modo de ejecución real del mecanismo de contingencia para Integración Continua (CI):

```
                                  ┌───────────────────────────────┐
                                  │   hf_embeddings.generate()    │
                                  └───────────────┬───────────────┘
                                                  │
                                   ¿Existe HF_TOKEN y Red?
                                                  │
                         ┌────────────────────────┴────────────────────────┐
                         │ SI                                              │ NO
                         ▼                                                 ▼
        ┌──────────────────────────────────┐             ┌──────────────────────────────────┐
        │  [MODE: HUGGINGFACE_REAL_MODEL]  │             │      [MODE: FALLBACK_CI]         │
        │ Inferencia con all-MiniLM-L6-v2  │             │ Proyección semántica 384d        │
        │ Embeddings neuronales densos     │             │ Determinismo estricto para CI    │
        └──────────────────────────────────┘             └──────────────────────────────────┘
```

### Tabla Comparativa de Modos de Ejecución:
| Parámetro / Característica | Entorno Real (Hugging Face API / Local) | Entorno de CI / Fallback Determinista |
| :--- | :--- | :--- |
| **Identificador de Modo en Logs** | `[MODE: HUGGINGFACE_REAL_MODEL]` | `[MODE: FALLBACK_CI]` |
| **Activación** | Token `HF_TOKEN` configurado y conexión de red activa | Ejecución en GitHub Actions sin secretos o modo offline |
| **Dimensión Resultante** | Exactamente 384 floats (`float32`) | Exactamente 384 floats (`float32`) |
| **Norma Euclidiana $L_2$** | $1.0000 \pm 10^{-4}$ (Normalizado) | $1.0000 \pm 10^{-4}$ (Normalizado) |
| **Uso en el Proyecto** | Indexación en base de datos real y producción | Ejecución de suite de tests automatizados en CI |

---

## 3. Evidencia Empírica de Ejecución (`test_hf_embeddings.py`)

Para verificar reproduciblemente la generación de embeddings, se ejecuta el script dedicado:
```bash
python scripts/evaluation/test_hf_embeddings.py
```

### Registro de Ejecución Real Obtenido:
```text
================================================================================
SENIORVITAL 2.0 - EVALUACION EMPIRICA DE EMBEDDINGS HUGGING FACE
================================================================================
[Config] Modelo Configurado: sentence-transformers/all-MiniLM-L6-v2
[Config] Dimension Esperada: 384
--------------------------------------------------------------------------------

[Muestra 1/3]: OA-01_SAMPLE - Osteoartritis de Rodilla y Cadera
[Texto]: "Queda estrictamente prohibida la prescripcion de ejercicios que incluyan pliometria (..."
[Modo Post-Ejecucion]: [HUGGINGFACE_REAL_MODEL]
[Tensor] Dimension: 384 float32 (Esperado: 384)
[Norma] Euclidiana L2: 1.0000 (Vector Unitario Normalizado)
[Floats] Primeros 5 Valores: [0.001616, -0.02928, 0.023609, -0.064185, 0.002837]

[Muestra 2/3]: SAR-02_SAMPLE - Sarcopenia y Dinapenia Geriatrica
[Texto]: "Prescripcion de entrenamiento de fuerza progresiva (PRT) al 40-80% 1-RM con bandas el..."
[Modo Post-Ejecucion]: [HUGGINGFACE_REAL_MODEL]
[Tensor] Dimension: 384 float32 (Esperado: 384)
[Norma] Euclidiana L2: 1.0000 (Vector Unitario Normalizado)
[Floats] Primeros 5 Valores: [-0.012771, 0.070441, -0.119277, -0.047018, -0.018115]

[Muestra 3/3]: ICC-04_SAMPLE - Insuficiencia Cardiaca Cronica e Hipertension
[Texto]: "Monitoreo cardiovascular estricto con escala Borg 11-12. Prohibido ejercicio si hay g..."
[Modo Post-Ejecucion]: [HUGGINGFACE_REAL_MODEL]
[Tensor] Dimension: 384 float32 (Esperado: 384)
[Norma] Euclidiana L2: 1.0000 (Vector Unitario Normalizado)
[Floats] Primeros 5 Valores: [-0.014726, 0.075218, -0.07605, 0.013499, -0.088733]

================================================================================
[SUCCESS] TODAS LAS PRUEBAS DE REPRESENTACION VECTORIAL (384d) SUPERADAS (MODO REAL: HUGGINGFACE_REAL_MODEL)
================================================================================
```

---

## 4. Trazabilidad con la Suite de Pruebas Automatizadas
* **Archivo de Pruebas:** [`tests/rag/test_embeddings.py`](../../tests/rag/test_embeddings.py)
* **Comando de Verificación:** `pytest tests/rag/test_embeddings.py -v`
* **Resultado:** Valida que la dimensión sea exactamente $384$, los tipos sean numéricos de punto flotante y no existan vectores nulos o vacíos.
