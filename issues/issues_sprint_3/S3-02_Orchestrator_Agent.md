# 🎛️ Issue S3-02: Diseño e Implementación del Orchestrator Agent (Supervisor)

**Materia:** Sistemas Inteligentes  
**Docente:** Dra. Yaskelly Yedra  
**Autores:** Daniel Alejandro Sánchez Ávila & Abdenago Nahmens  
**Proyecto:** SeniorVital 2.0 — Sistemas Multiagentes y Orquestación  
**Sprint Técnico:** Sprint 3 — Arquitectura Multiagente y Supervisor Pattern  

---

## 🎯 1. Responsabilidades del Orchestrator Agent

El `MultiAgentOrchestrator` implementado en `app/agents/multi_agent_orchestrator.py` actúa como el nodo raíz del sistema:

1. **Gestión de Identificadores de Traza (`trace_id`):** Genera un ID único para cada sesión para garantizar la observabilidad de extremo a extremo.
2. **Control de Flujo Secuencial (Pipeline A2A):**
   * **Fase 1 (Analítica):** Invoca a `AnalyticsAgent` para evaluar adherencia y riesgo.
   * **Fase 2 (Empatía):** Invoca a `MotivationAgent` para preparar el tono afectivo adaptado.
   * **Fase 3 (Razonamiento Clínico):** Invoca a `WellnessCoachAgent` con el patrón ReAct y RAG.
   * **Fase 4 (Control de Calidad):** Invoca a `QAArchitectAgent` para validar guardrails.
3. **Consolidación de Salida:** Agrega métricas, trazas de tiempo (`elapsed_ms`) y respuesta final en una estructura JSON transparente.

---

## 💻 2. Código Central de la Orquestación

```python
class MultiAgentOrchestrator:
    async def orchestrate_request(self, user_id: str, query: str, user_role: str = "senior") -> Dict[str, Any]:
        # 1. Analytics
        analytics = await self.analytics_agent.analyze_patient_progression(uid)
        # 2. Motivation
        motivation = await self.motivation_agent.generate_encouragement(analytics["adherence_rate"])
        # 3. Clinical Coach
        coach = await self.wellness_coach.execute_react_cycle(user_id=str(uid), query=query)
        # 4. QA Audit
        qa = self.qa_agent.audit_response(coach.get("response", ""))
        return payload
```
