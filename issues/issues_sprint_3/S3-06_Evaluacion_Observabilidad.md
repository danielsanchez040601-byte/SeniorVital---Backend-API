# 📊 Issue S3-06: Evaluación de Rendimiento, Trazabilidad y Observabilidad Multiagente

**Materia:** Sistemas Inteligentes  
**Docente:** Dra. Yaskelly Yedra  
**Equipo:** Team 5  
**Autores:** Daniel Alejandro Sánchez Ávila & Abdenago Nahmens  
**Proyecto:** SeniorVital 2.0 — Sistemas Multiagentes y Orquestación  
**Sprint Técnico:** Sprint 3 — Arquitectura Multiagente y Supervisor Pattern  
**Estado:** Implementado — pendiente de aprobación docente  

---

## 📈 1. Resumen de Métricas del Benchmark Reproducible (S3-06)

Ejecutamos la evaluación cuantitativa automatizada mediante `scripts/evaluation/evaluate_multiagent.py` sobre `data/evaluation/multiagent_scenarios.json`:

* **Precisión de Delegación (Enrutamiento):** **100.0%** (6/6 escenarios dirigidos al agente correcto o fallback seguro).
* **Tasa de Adherencia Clínica para Adultos Mayores (+60 años):** **100.0%** (100% de cumplimiento en advertencias de sodio, hidratación y restricciones clínicas).
* **Puntuación Media de Adherencia Heurística:** **100.0%**.
* **Latencia Media de Orquestación:** **0.31 ms** (Percentil 95: **0.67 ms**).
* **Bloqueo Preventivo ISO/IEC 25010:** **100%** de efectividad ante sugerencias farmacológicas o peligrosas (MA05).

El informe detallado de cada escenario y el desglose de calidad clínica se encuentra en [S3-06_Evaluacion_Multiagente.md](./S3-06_Evaluacion_Multiagente.md).

---

## 🔬 2. Trazabilidad Estructurada por Eventos (`OrchestrationLogger`)

Cada solicitud procesada por el supervisor emite eventos JSON trazables mediante `correlation_id`:
1. `dispatch_start`: registro de la consulta de entrada, usuario e intención previa.
2. `intent_classified`: dominio resultante y confianza obtenida (fast-path léxico o LLM).
3. `agent_selected`: agente especializado al que se despacha la tarea (`nutrition` o `wellness_coach`).
4. `safety_check`: auditoría determinística de guardrails antes de emitir la respuesta.
5. `dispatch_end`: consolidación de tiempos de ejecución (`duration_ms`) y bandera de bloqueo.
