# 🎛️ Issue S3-02: Diseño e Implementación del Orchestrator Agent (Supervisor Centralizado)

**Materia:** Sistemas Inteligentes  
**Docente:** Dra. Yaskelly Yedra  
**Autores:** Daniel Alejandro Sánchez Ávila & Abdenago Nahmens  
**Proyecto:** SeniorVital 2.0 — Sistemas Multiagentes y Orquestación  
**Sprint Técnico:** Sprint 3 — Arquitectura Multiagente y Supervisor Pattern  
**Estado:** ✅ APROBADO Y CERRADO TRAS AUDITORÍA DE SPRINT 3  

---

## 🎯 1. Responsabilidades del Orchestrator Agent Centralizado

Unificamos la arquitectura tomando como **única fuente de verdad** el motor dinámico en `src/orchestration/`:
- El módulo rígido anterior en `app/agents/multi_agent_orchestrator.py` fue depurado y redirigido para mantener compatibilidad legacy sin interferir en el runtime.
- El núcleo operativo reside en `src/orchestration/router.py` bajo la clase `OrchestratorAgent`.

### Capacidades Implementadas:
1. **Clasificación Dinámica de Intenciones (`IntentClassifier`):**
   - **Fast-Path Léxico:** Mapeo de términos de alta frecuencia en salud gerontológica (nutrición, ejercicio, seguridad, dolor, medicamentos). Si la confianza supera el umbral (0.7), enruta inmediatamente sin invocar al LLM.
   - **Clasificador Semántico LLM:** Si la consulta es compleja, invoca al modelo de lenguaje con un prompt estructurado en JSON para determinar el dominio.
2. **Despacho Dinámico (`dispatch`):**
   - Recibe instancias tipadas de `DispatchRequest` desde el endpoint `/api/v1/chat`.
   - Selecciona el agente idóneo (`NutritionAgent`, `WellnessCoachAgent` o agentes de soporte) en función de la intención clasificada.
   - Activa el agente de fallback (`WellnessCoachAgent`) en caso de intenciones generales o contingencias.
3. **Control Anti-Ciclos y Trazabilidad:**
   - Detecta reentradas con el mismo `correlation_id` mediante el conjunto `_active_correlations`, arrojando `OrchestrationError` si se detecta recursión no controlada.
   - Emite telemetría estructurada mediante `OrchestrationLogger` (`dispatch_start`, `agent_selected`, `dispatch_end`).

---

## 💻 2. Implementación Canónica de Orquestación (`src/orchestration/router.py`)

```python
class OrchestratorAgent:
    """Orquestador centralizado que clasifica la intención y delega a agentes especializados."""

    def __init__(self, llm: LLMService) -> None:
        self._llm = llm
        self._agents: dict[str, Any] = {}
        self._classifier = IntentClassifier(llm)
        self._fallback_agent: Any = None
        self._active_correlations: set[str] = set()

    async def dispatch(self, request: DispatchRequest) -> DispatchResponse:
        correlation_id = request.correlation_id or request.request_id
        
        # 1. Anti-ciclos
        if correlation_id in self._active_correlations:
            raise OrchestrationError(f"Delegation cycle detected: {correlation_id}")
        self._active_correlations.add(correlation_id)

        try:
            # 2. Clasificación de intención
            intent = await self._classifier.classify(request.message) if not request.intent else ...

            # 3. Selección y delegación dinámica
            agent = self.select_agent(intent)
            response = await agent.handle(AgentRequest(
                message=request.message,
                user_id=request.user_id,
                context={"correlation_id": correlation_id}
            ))

            # 4. Verificación de seguridad crítica
            blocked = response.safety_level == "critical"
            return response_to_dispatch_response(
                response,
                request_id=request.request_id,
                agent=getattr(agent, "name", "unknown"),
                intent=intent.domain,
                blocked=blocked
            )
        finally:
            self._active_correlations.discard(correlation_id)
```

---

## 🔗 3. Conexión de Extremo a Extremo con el Endpoint `/api/v1/chat`

En `src/api/chat.py`, el endpoint `/chat` fue refactorizado para instanciar e inyectar el supervisor:
- Delega consultas de dieta, alimentos e hidratación directamente al `NutritionAgent`.
- Delega consultas de dolor articular, acondicionamiento físico o progreso al `WellnessCoachAgent`.
- Devuelve `ChatResponse` con telemetría estructurada, `correlation_id` y tiempo de ejecución.
