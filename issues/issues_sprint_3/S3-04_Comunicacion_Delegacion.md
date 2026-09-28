# 📡 Issue S3-04: Protocolo Unificado de Comunicación y Delegación Interagente (A2A)

**Materia:** Sistemas Inteligentes  
**Docente:** Dra. Yaskelly Yedra  
**Equipo:** Team 5  
**Autores:** Daniel Alejandro Sánchez Ávila & Abdenago Nahmens  
**Proyecto:** SeniorVital 2.0 — Sistemas Multiagentes y Orquestación  
**Sprint Técnico:** Sprint 3 — Arquitectura Multiagente y Supervisor Pattern  
**Estado:** Implementado — pendiente de aprobación docente  

---

## 📨 1. Protocolo de Mensajería Unificado: `DispatchRequest` y `AgentMessage`

En cumplimiento de las observaciones de revisión, consolidamos el protocolo de comunicación en `src/orchestration/`:
- **`DispatchRequest` (`src/orchestration/dispatch.py`):** Contrato formal entre el API Gateway (`/api/v1/chat`) y el `OrchestratorAgent`. Transporta la consulta del usuario, perfil, contexto, historial e identificador de correlación.
- **`DispatchResponse` (`src/orchestration/dispatch.py`):** Estructura devuelta al endpoint con el texto generado, nombre del agente que atendió la tarea, dominio de intención, herramientas ejecutadas, nivel de seguridad y telemetría de tiempos (`duration_ms`).
- **`AgentMessage` (`src/orchestration/agent_protocol.py`):** Contrato wire interno de comunicación A2A. Asegura que los agentes no mantengan referencias acopladas al orquestador.

```python
@dataclass
class DispatchRequest:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    user_id: int = 0
    message: str = ""
    intent: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    conversation_history: list[dict[str, Any]] = field(default_factory=list)
    correlation_id: str = ""
```

---

## 🛡️ 2. Prevención de Ciclos, Anti-Recursión y Trazabilidad de Extremo a Extremo

1. **Propagación del `correlation_id`:** Generado en `/api/v1/chat`, viaja dentro de cada `DispatchRequest`, se inyecta en el contexto de cada `AgentRequest` y se registra en cada evento estructurado de `OrchestrationLogger` (`dispatch_start`, `agent_selected`, `dispatch_end`).
2. **Control Anti-Ciclos en Tiempo de Ejecución:** El `OrchestratorAgent` mantiene un conjunto `_active_correlations`. Si una solicitud reentrante porta un `correlation_id` que ya está activo en la pila de ejecución, el supervisor aborta inmediatamente elevando un `OrchestrationError`.
3. **Colaboración Inter-Agente Mediante `WorkflowEngine` (`src/orchestration/protocol.py`):** Permite encadenar agentes de forma condicionada sin ciclos. Por ejemplo, en el escenario MA06:
   - Paso 1: `WellnessCoachAgent` recupera el progreso físico de la rutina de hoy.
   - Paso 2: `NutritionAgent` (Team 5) recibe el contexto `{prev.text}` y prescribe recomendaciones alimentarias adaptadas al esfuerzo realizado.

---

## 🧪 3. Verificación de Integración

El protocolo fue verificado mediante la suite de integración en `tests/integration/test_multiagent_flow.py` y `tests/integration/test_s3_collaboration.py`, validando que:
- Se emitan todos los eventos estructurados con el mismo `correlation_id`.
- La delegación entre `OrchestratorAgent` y los agentes de dominio (`NutritionAgent` y `WellnessCoachAgent`) opere de manera transparente y determinista.
- Las solicitudes bloqueadas por guardrails críticos retornen `blocked: true` con mensaje preventivo estandarizado.
