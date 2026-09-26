# 📡 Issue S3-04: Protocolo de Comunicación y Delegación Interagente (A2A)

**Materia:** Sistemas Inteligentes  
**Docente:** Dra. Yaskelly Yedra  
**Autores:** Daniel Alejandro Sánchez Ávila & Abdenago Nahmens  
**Proyecto:** SeniorVital 2.0 — Sistemas Multiagentes y Orquestación  
**Sprint Técnico:** Sprint 3 — Arquitectura Multiagente y Supervisor Pattern  

---

## 📨 1. Formato Estructurado de Mensajes A2A

Para garantizar la interoperabilidad y evitar dependencias cíclicas, todos los agentes intercambian diccionarios serializables con esquema homogéneo:

```json
{
  "trace_id": "a1b2c3d4",
  "step_index": 1,
  "source_agent": "SupervisorOrchestrator",
  "target_agent": "AnalyticsAgent",
  "payload": {
    "user_id": 1,
    "query_context": "Evaluación de progresión clínica a 14 días"
  },
  "timestamp": "2026-08-29T00:50:00Z"
}
```

---

## 🛡️ 2. Mecanismos de Prevención de Ciclos Infinitos y Timeouts

1. **Grafo Acíclico Dirigido (DAG):** El flujo avanza en una sola dirección: $\text{Supervisor} \to \text{Analytics} \to \text{Motivation} \to \text{Coach} \to \text{QA} \to \text{Supervisor}$.
2. **Timeouts Defensivos:** Cada invocación LLM o de base de datos tiene un límite máximo de ejecución ($14.0\text{s}$ para LLM, $5.0\text{s}$ para consultas SQL).
3. **Fallback Determinístico por Agente:** Si cualquier agente especializado arroja una excepción, el supervisor captura el error y utiliza valores por defecto seguros sin abortar la respuesta completa.
