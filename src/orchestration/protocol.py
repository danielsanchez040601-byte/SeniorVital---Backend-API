"""Interaction Protocol — mecanismos de comunicación inter-agente.

Define:
- DelegateCallback: protocolo inyectable para que agentes deleguen sin conocer al orchestrator.
- WorkflowStep: paso de un workflow multi-agente.
- WorkflowEngine: motor que ejecuta workflows encadenando agentes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from src.orchestration.agent_protocol import AgentResponse
from src.orchestration.logging import OrchestrationLogger, create_timer

logger = logging.getLogger(__name__)

# Shared logger instance for all protocol components
_orchestration_log = OrchestrationLogger()


@runtime_checkable
class DelegateCallback(Protocol):
    """Protocolo para delegación de tareas entre agentes.

    Se inyecta en agentes que necesitan solicitar ayuda a otros agentes
    sin mantener una referencia directa al OrchestratorAgent.

    Ejemplo de uso dentro de un agente::

        class MyAgent:
            def __init__(self, delegate_callback: DelegateCallback):
                self._delegate = delegate_callback

            async def process(self, user_id, message):
                # Necesito info de nutrición
                result = await self._delegate(
                    from_agent="analytics",
                    to_agent="nutrition",
                    task={"message": "diabetes restricciones", "user_id": user_id}
                )
                return result
    """

    async def __call__(
        self, from_agent: str, to_agent: str, task: dict
    ) -> dict:
        """Delega una tarea a otro agente.

        Args:
            from_agent: Nombre del agente que delega.
            to_agent: Nombre del agente destino.
            task: Payload de la tarea (message, user_id, context, etc.).

        Returns:
            Resultado de la tarea delegada.
        """
        ...


@dataclass
class WorkflowStep:
    """Paso de un workflow multi-agente.

    Attributes:
        agent: Nombre del agente que procesa este paso.
        task_template: Payload con placeholders {prev.result}, {prev.text}, etc.
        condition: Expresión simple para condicionar la ejecución.
                   Si es None, el paso siempre se ejecuta.
                   Ej: "prev.safety_level != 'critical'"
        step_id: Identificador único del paso (para trazabilidad).
    """

    agent: str
    task_template: dict[str, Any]
    condition: str | None = None
    step_id: str = ""


@dataclass
class StepResult:
    """Resultado de la ejecución de un paso de workflow.

    Attributes:
        step_id: Identificador del paso.
        agent: Agente que procesó.
        success: Si el paso completó sin error.
        response: Respuesta del agente (AgentResponse o None si falló).
        skipped: Si el paso fue saltado por condición.
        error: Mensaje de error si falló.
        duration_ms: Tiempo de ejecución en milisegundos.
    """

    step_id: str
    agent: str
    success: bool
    response: AgentResponse | None = None
    skipped: bool = False
    error: str = ""
    duration_ms: float = 0.0


class WorkflowEngine:
    """Motor de workflows multi-agente.

    Ejecuta una secuencia de pasos, pasando el resultado de cada paso
    al siguiente. Soporta condiciones para saltar pasos.

    Precondiciones:
        - OrchestratorAgent con agentes registrados.
        - Los agentes referenciados en los pasos existen.

    Postcondiciones:
        - execute() retorna la lista de StepResult con el resultado de cada paso.
        - El resultado final contiene la respuesta del último paso exitoso.

    Efectos secundarios:
        - Ejecuta agentes que pueden modificar estado.
        - Registra eventos de logging para cada paso.
    """

    def __init__(self, orchestrator: Any) -> None:
        """Inicializa el motor con referencia al orquestador.

        Args:
            orchestrator: Instancia de OrchestratorAgent.
        """
        self._orchestrator = orchestrator
        self._log = OrchestrationLogger()

    async def execute(
        self,
        steps: list[WorkflowStep],
        initial_context: dict[str, Any],
        correlation_id: str = "",
    ) -> list[StepResult]:
        """Ejecuta un workflow paso a paso.

        Args:
            steps: Lista ordenada de pasos a ejecutar.
            initial_context: Contexto inicial (user_id, message, etc.).
            correlation_id: ID de correlación para trazabilidad.

        Returns:
            Lista de StepResult con el resultado de cada paso.
        """
        results: list[StepResult] = []
        prev_result: StepResult | None = None

        for i, step in enumerate(steps):
            step_id = step.step_id or f"step_{i}"

            # Evaluar condición
            if step.condition and prev_result is not None:
                if not self._evaluate_condition(step.condition, prev_result):
                    self._log.workflow_step(
                        correlation_id, i, step.agent, skipped=True
                    )
                    results.append(StepResult(
                        step_id=step_id,
                        agent=step.agent,
                        success=True,
                        skipped=True,
                    ))
                    continue

            # Construir task desde template + resultado anterior
            task = self._build_task(step.task_template, initial_context, prev_result)

            # Ejecutar paso
            timer = create_timer()
            try:
                delegate_result = await self._orchestrator.delegate(
                    from_agent="workflow",
                    to_agent=step.agent,
                    task=task,
                    correlation_id=correlation_id,
                )

                duration = timer[0]()

                # Convertir dict a AgentResponse si es necesario
                if isinstance(delegate_result, dict):
                    response = AgentResponse(
                        text=delegate_result.get("text", ""),
                        safety_level=delegate_result.get("safety_level", "safe"),
                        tool_chain=delegate_result.get("tool_chain", []),
                        metadata=delegate_result.get("metadata", {}),
                    )
                else:
                    response = delegate_result

                step_result = StepResult(
                    step_id=step_id,
                    agent=step.agent,
                    success=True,
                    response=response,
                    duration_ms=duration,
                )

                self._log.workflow_step(correlation_id, i, step.agent)

            except Exception as e:
                duration = timer[0]()
                logger.error(f"Workflow step {step_id} failed: {e}")
                step_result = StepResult(
                    step_id=step_id,
                    agent=step.agent,
                    success=False,
                    error=str(e),
                    duration_ms=duration,
                )

            results.append(step_result)
            prev_result = step_result

        return results

    def _build_task(
        self,
        template: dict[str, Any],
        initial_context: dict[str, Any],
        prev_result: StepResult | None,
    ) -> dict[str, Any]:
        """Construye el task desde el template, contexto inicial y resultado anterior.

        Soporta placeholders:
        - {prev.text}: texto de la respuesta del paso anterior
        - {prev.safety_level}: nivel de seguridad del paso anterior
        - {ctx.user_id}: user_id del contexto inicial
        - {ctx.message}: message del contexto inicial
        """
        task = {}
        for key, value in template.items():
            if isinstance(value, str):
                value = self._resolve_placeholder(value, initial_context, prev_result)
            elif isinstance(value, dict):
                value = {
                    k: self._resolve_placeholder(v, initial_context, prev_result)
                    if isinstance(v, str)
                    else v
                    for k, v in value.items()
                }
            task[key] = value
        return task

    def _resolve_placeholder(
        self,
        value: str,
        initial_context: dict[str, Any],
        prev_result: StepResult | None,
    ) -> Any:
        """Resuelve un placeholder en un string."""
        if not isinstance(value, str) or "{" not in value:
            return value

        # {prev.text}
        if "{prev.text}" in value and prev_result and prev_result.response:
            value = value.replace("{prev.text}", prev_result.response.text)

        # {prev.safety_level}
        if "{prev.safety_level}" in value and prev_result and prev_result.response:
            value = value.replace("{prev.safety_level}", prev_result.response.safety_level)

        # {ctx.user_id}
        if "{ctx.user_id}" in value:
            value = value.replace("{ctx.user_id}", str(initial_context.get("user_id", 0)))

        # {ctx.message}
        if "{ctx.message}" in value:
            value = value.replace("{ctx.message}", initial_context.get("message", ""))

        return value

    def _evaluate_condition(self, condition: str, prev_result: StepResult) -> bool:
        """Evalúa una condición simple sobre el resultado anterior.

        Soporta:
        - "prev.safety_level != 'critical'"
        - "prev.success == True"
        - "prev.skipped == False"
        """
        try:
            # Reemplazar referencias al resultado
            expr = condition
            if prev_result:
                expr = expr.replace("prev.safety_level", repr(prev_result.response.safety_level if prev_result.response else "safe"))
                expr = expr.replace("prev.success", repr(prev_result.success))
                expr = expr.replace("prev.skipped", repr(prev_result.skipped))
            return bool(eval(expr, {"__builtins__": {}}))
        except Exception as e:
            logger.warning(f"Failed to evaluate condition '{condition}': {e}")
            return True  # Default: ejecutar el paso si la condición falla
