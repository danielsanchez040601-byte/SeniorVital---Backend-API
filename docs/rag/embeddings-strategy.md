# 🧬 Estrategia de Representación Vectorial (Embeddings)

> **Materia:** Sistemas Inteligentes — Dra. Yaskelly Yedra  
> **Autores:** Daniel Sánchez & Abdenago Nahmens | **Asesoría Clínica:** Ing. Julio Matute  

---

## 1. Selección del Modelo
* **Modelo:** `sentence-transformers/all-MiniLM-L6-v2` (vía Hugging Face Inference API y fallback local).
* **Dimensionalidad:** 384 dimensiones continuas.
* **Métrica de Distancia:** Distancia de Coseno ($1 - \cos(	heta)$).
* **Justificación FinOps / Eficiencia:**
  - $0 costo operativo (Hugging Face Serverless API).
  - Tiempo de inferencia $< 60\text{ ms}$ por batch.
  - Memoria compacta en base de datos PostgreSQL ($1.5\text{ KB}$ por vector indexado).
