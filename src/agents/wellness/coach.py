"""Wellness Coach Agent 2.0 — agente conversacional cognitivo.

Extiende WellnessAgent con:
- Tool calling (8 herramientas)
- Memoria conversacional (MemoryStore)
- Razonamiento ReAct (max 3 iteraciones)
- Prompt parametrizable
"""

import logging
from datetime import date

from src.agents.wellness.agent import WellnessAgent
from src.agents.wellness.config import WellnessConfig
from src.agents.wellness.prompts.wellness_coach import WellnessCoachPromptBuilder
from src.agents.wellness.reasoning import ReActEngine
from src.memory import MemoryStore, Message
from src.services.llm import LLMService
from src.services.user_data import UserDataService
from src.tools import Tool, ToolResult

logger = logging.getLogger(__name__)


class WellnessCoachAgent:
    """Agente conversacional cognitivo con tool calling y ReAct.

    Precondiciones:
        - LLMService con conexión a Ollama activa.
        - Herramientas inyectadas y funcionales.
        - MemoryStore implementado (puede ser None para modo sin memoria).

    Postcondiciones:
        - Retorna respuesta personalizada basada en razonamiento.
        - Historial conversacional actualizado (si memory_store != None).

    Efectos secundarios:
        - Ejecuta herramientas que pueden modificar BD (log_habit, generate_routine).
        - Persiste mensajes en memory_store.
    """

    def __init__(
        self,
        llm: LLMService,
        user_data: UserDataService,
        tools: list[Tool],
        memory_store: MemoryStore | None = None,
        config: WellnessConfig | None = None,
    ) -> None:
        self._llm = llm
        self._user_data = user_data
        self._tools = tools
        self._memory = memory_store
        self._config = config or WellnessConfig()
        self._prompt_builder = WellnessCoachPromptBuilder()
        self._react_engine = ReActEngine(
            llm=llm,
            tools=tools,
            max_iterations=self._config.max_react_iterations,
            tool_failure_threshold=self._config.tool_failure_threshold,
        )

    async def chat(self, user_id: int, message: str) -> str:
        """Procesa un mensaje del usuario y retorna una respuesta.

        Flujo:
            1. Obtener historial conversacional.
            2. Construir prompt con perfil + historial.
            3. Ejecutar ciclo ReAct (observe→think→act).
            4. Guardar mensajes en memoria.
            5. Retornar respuesta.

        Args:
            user_id: ID del usuario.
            message: Mensaje del usuario.

        Returns:
            Respuesta del coach en texto plano.
        """
        user_str_id = str(user_id)

        # 1. Obtener historial
        history: list[Message] = []
        if self._memory:
            try:
                history = await self._memory.get_history(
                    user_str_id, limit=self._config.conversation_history_limit
                )
            except Exception as e:
                logger.warning(f"Failed to get history: {e}")

        # 2. Obtener perfil del usuario
        user_profile = await self._get_user_profile(user_id)

        # 3. Construir prompt
        system_prompt, user_prompt = self._prompt_builder.build(
            user_message=message,
            user_profile=user_profile,
            conversation_history=history,
            available_tools=self._tools,
        )

        # 4. Ejecutar ReAct
        trace = await self._react_engine.run(system_prompt, user_prompt)

        logger.info(
            f"ReAct trace: {trace.iterations} iterations, "
            f"{len(trace.steps)} steps, "
            f"final_answer={trace.final_answer[:100]}..."
        )
        for i, step in enumerate(trace.steps):
            logger.debug(
                f"  Step {i + 1}: thought={step.thought[:60]}... "
                f"action={step.action or '(direct)'} "
                f"tool_success={step.tool_result.success if step.tool_result else 'N/A'}"
            )

        # 4.1 Fallback si la respuesta está vacía
        if not trace.final_answer or not trace.final_answer.strip():
            trace.final_answer = (
                "Disculpa, no pude procesar tu solicitud en este momento. "
                "¿Podrías reformularla o preguntar sobre algo diferente?"
            )

        # 5. Guardar en memoria
        if self._memory:
            try:
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc).isoformat()

                await self._memory.add_message(
                    user_str_id,
                    Message(role="user", content=message, timestamp=now),
                )
                await self._memory.add_message(
                    user_str_id,
                    Message(role="assistant", content=trace.final_answer, timestamp=now),
                )
            except Exception as e:
                logger.warning(f"Failed to save to memory: {e}")

        return trace.final_answer

    async def _get_user_profile(self, user_id: int) -> dict:
        """Obtiene el perfil del usuario para el prompt.

        Returns:
            Dict con profile, health_profile, preferences.
        """
        try:
            data = await self._user_data.get_user_data(user_id)
            return {
                "name": data.profile.get("name", ""),
                "age": data.profile.get("age", ""),
                "city": data.profile.get("city", ""),
                "health": data.health_profile,
                "preferences": data.preferences,
            }
        except Exception as e:
            logger.warning(f"Failed to get user profile for {user_id}: {e}")
            return {"user_id": user_id}
