"""ReAct Engine — motor de razonamiento observe→think→act."""

import json
import logging
from dataclasses import dataclass, field

from src.services.llm import LLMService
from src.tools import Tool, ToolResult

logger = logging.getLogger(__name__)


@dataclass
class ReActStep:
    """Un paso del ciclo ReAct."""

    observation: str = ""
    thought: str = ""
    action: str = ""
    action_input: dict = field(default_factory=dict)
    tool_result: ToolResult | None = None


@dataclass
class ReActTrace:
    """Traza completa del ciclo ReAct."""

    steps: list[ReActStep] = field(default_factory=list)
    final_answer: str = ""
    iterations: int = 0


class ReActEngine:
    """Motor de razonamiento ReAct: observe→think→act.

    Ejecuta un ciclo donde el LLM razona en cada iteración,
    decide si usar una herramienta o responder directamente.

    Precondiciones: LLMService inicializado, herramientas listas.
    Postcondiciones: ReActTrace con traza completa y respuesta final.
    Efectos secundarios: Ejecuta herramientas (side effects de cada tool).
    """

    def __init__(
        self,
        llm: LLMService,
        tools: list[Tool],
        max_iterations: int = 3,
        tool_failure_threshold: int = 2,
    ) -> None:
        self._llm = llm
        self._tools = {t.name: t for t in tools}
        self._max_iterations = max_iterations
        self._tool_failure_threshold = tool_failure_threshold

    async def run(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> ReActTrace:
        """Ejecuta el ciclo ReAct completo.

        Flujo por iteración:
            1. LLM genera respuesta con system prompt separado.
            2. Parser extrae {thought, action, action_input} o {thought, final_answer}.
            3. Si final_answer → salir del ciclo.
            4. Si action → ejecutar tool, append resultado al contexto.
            5. Repetir hasta max_iterations o final_answer.

        Args:
            system_prompt: System prompt que describe el rol y formato ReAct.
            user_prompt: Prompt del usuario con contexto.

        Returns:
            ReActTrace con la traza del razonamiento y respuesta final.
        """
        trace = ReActTrace()
        context = user_prompt
        consecutive_failures = 0

        for i in range(self._max_iterations):
            logger.info(f"ReAct iteration {i + 1}/{self._max_iterations}")

            response = await self._llm.generate(
                context,
                system=system_prompt,
                format_json=True,
            )

            step = self._parse_response(response)
            trace.steps.append(step)
            trace.iterations = i + 1

            logger.debug(
                f"ReAct step {i + 1}: thought={step.thought[:80]}... "
                f"action={step.action or '(final_answer)'}"
            )

            # Final answer detectado → salir del ciclo
            if not step.action:
                trace.final_answer = step.observation or response
                break

            # Ejecutar herramienta
            tool = self._tools.get(step.action)
            if not tool:
                step.tool_result = ToolResult(
                    success=False,
                    error=f"Herramienta '{step.action}' no disponible",
                    tool_name=step.action,
                )
            else:
                try:
                    step.tool_result = await tool.execute(**step.action_input)
                except Exception as e:
                    step.tool_result = ToolResult(
                        success=False,
                        error=str(e),
                        tool_name=step.action,
                    )

            logger.debug(
                f"ReAct tool result: {step.action} "
                f"success={step.tool_result.success}"
            )

            # Construir observación para el contexto
            if step.tool_result.success and step.tool_result.data:
                result_text = json.dumps(
                    step.tool_result.data, ensure_ascii=False
                )
            else:
                result_text = f"Error: {step.tool_result.error}"

            # Feed resultado al contexto para la siguiente iteración
            observation = (
                f"Resultado de {step.action}: {result_text}\n\n"
                "Ahora decide: ¿necesitas otra herramienta o puedes responder?"
            )
            step.observation = observation
            context = f"{user_prompt}\n\n{self._build_observations_history(trace.steps)}"

            # Control de fallos consecutivos
            if not step.tool_result.success:
                consecutive_failures += 1
                logger.warning(
                    f"Tool {step.action} failed ({consecutive_failures}/"
                    f"{self._tool_failure_threshold}): {step.tool_result.error}"
                )
                if consecutive_failures >= self._tool_failure_threshold:
                    logger.warning(
                        f"Consecutive failure threshold reached "
                        f"({self._tool_failure_threshold}). Aborting cycle."
                    )
                    break
            else:
                consecutive_failures = 0

        else:
            # Max iterations alcanzado
            trace.final_answer = (
                trace.steps[-1].thought if trace.steps else "No se pudo completar."
            )

        return trace

    def _build_observations_history(self, steps: list[ReActStep]) -> str:
        """Construye un resumen de las observaciones previas para el contexto."""
        parts = []
        for i, step in enumerate(steps):
            if step.observation:
                parts.append(f"[Paso {i + 1}] {step.observation}")
        return "\n".join(parts)

    def _parse_response(self, response: str) -> ReActStep:
        """Parsea la respuesta del LLM en un ReActStep.

        Busca JSON con {thought, action, action_input} o {thought, final_answer}.
        Fallback: trata como respuesta directa (final_answer implícito).
        """
        step = ReActStep()

        try:
            cleaned = response.strip()

            # Limpiar TODOS los artefactos de markdown fences
            if "```" in cleaned:
                lines = cleaned.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                cleaned = "\n".join(lines).strip()

            # Si hay múltiples objetos JSON separados por \n\n, intentar parsear el último
            # que tiene final_answer
            if "\n\n" in cleaned:
                parts = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
                # Buscar el que tiene final_answer
                for part in reversed(parts):
                    try:
                        parsed = json.loads(part)
                        if "final_answer" in parsed:
                            step.thought = parsed.get("thought", "")
                            step.observation = parsed["final_answer"]
                            step.action = ""
                            logger.debug(f"Found final_answer in multi-JSON response")
                            return step
                    except json.JSONDecodeError:
                        continue
                # Si no hay final_found, parsear el primero
                cleaned = parts[0]

            parsed = json.loads(cleaned)

            step.thought = parsed.get("thought", "")

            # FinalAnswer explícito
            if "final_answer" in parsed:
                step.observation = parsed["final_answer"]
                step.action = ""
                return step

            # Action con tool
            step.action = parsed.get("action", "")
            step.action_input = parsed.get("action_input", {})
            step.observation = step.thought or response
            return step

        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback: texto plano → final_answer implícito
        step.observation = response
        step.thought = response
        return step
