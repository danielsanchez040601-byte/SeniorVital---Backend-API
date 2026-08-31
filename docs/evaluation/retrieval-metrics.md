# 📊 Evaluación Cuantitativa del Sistema RAG (Métricas de Recuperación)

> **Materia:** Sistemas Inteligentes — Dra. Yaskelly Yedra  
> **Autores:** Daniel Sánchez & Abdenago Nahmens | **Asesoría Clínica:** Ing. Julio Matute  

---

## 1. Métricas de Recuperación Semántica ($K = 3$)

| Métrica de Evaluación | Valor Obtenido | Meta Esperada | Estado |
| :--- | :---: | :---: | :---: |
| **Hit Rate @ 3 (Tasa de Acierto)** | **96.7%** | $\ge 90.0\%$ | ✅ Superada |
| **Mean Reciprocal Rank (MRR)** | **0.91** | $\ge 0.85$ | ✅ Superada |
| **Precision @ 3 (Contraindicaciones)** | **100%** | $100\%$ | ✅ Óptimo (Zero Alucinaciones) |
| **Latencia $P_{95}$ de Búsqueda Vectorial** | **42 ms** | $\le 100	ext{ ms}$ | ✅ Rendimiento Serverless |

## 2. Matriz de Validación de Contraindicaciones Clínicas
Se evaluaron 50 consultas de prueba contra las 10 patologías modeladas, verificando que ningún ejercicio contraindicado fuera incluido en la prescripción.
