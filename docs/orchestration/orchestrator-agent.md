# Orchestrator Agent — Especificación Técnica y Contratos de Servicio

## 1. Misión del Orquestador

El **Orchestrator Agent** es el componente supervisor del Sprint 3 de SeniorVital. Coordina la comunicación inter-agente y la consolidación de respuestas, desacoplando la lógica de negocio de cada agente especializado y asegurando el cumplimiento de los estándares de calidad ISO/IEC 25010 y accesibilidad WCAG 2.1 AA.

## 2. Puntos de Entrada y Esquemas de Datos

### Solicitud de Entrada (`AgentRequest`)
```json
{
  "user_id": 1,
  "message": "¿Puedo hacer sentadillas hoy si me molestan un poco las rodillas?",
  "user_role": "senior",
  "context": {
    "session_id": "sess_8941",
    "fitness_level": 1
  }
}
```

### Respuesta Consolidada (`AgentResponse`)
```json
{
  "trace_id": "a4f89d1b",
  "user_id": 1,
  "user_role": "senior",
  "final_response": "¡Bienvenido/a! Su constancia es admirable. Con respecto a sus rodillas, para la artrosis no es conveniente realizar sentadillas profundas. Le recomiendo sentadillas parciales asistidas con silla o elevaciones de talones.",
  "analytics_summary": {
    "adherence": "85.0%",
    "risk_level": "GREEN",
    "avg_rpe": 4.1
  },
  "motivational_nudge": "Cada paso y movimiento suma a su independencia diaria.",
  "qa_status": "APPROVED",
  "total_elapsed_ms": 245.5,
  "execution_traces": [
    {"agent": "AnalyticsAgent", "elapsed_ms": 32.1},
    {"agent": "MotivationAgent", "elapsed_ms": 1.2},
    {"agent": "WellnessCoachAgent", "elapsed_ms": 204.8},
    {"agent": "QAArchitectAgent", "elapsed_ms": 0.8, "is_approved": true}
  ]
}
```

## 3. Principios de Observabilidad y Telemetría

- **Correlación de Petición a Fin:** Cada interacción mantiene el mismo `trace_id` a lo largo de todos los logs y mensajes A2A.
- **Registro de Tiempos y Proveedores:** El orquestador mide la latencia de cada agente y propaga el proveedor de LLM y modo de vector store efectivos utilizados en la consulta clínica.
- **Auditoría Transparente:** La bitácora registra las evaluaciones del `QAArchitectAgent`, permitiendo auditar violaciones bloqueadas y evaluar la estabilidad de los guardrails clínicos.
