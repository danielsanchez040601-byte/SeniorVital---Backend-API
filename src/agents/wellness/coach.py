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
from src.agents.wellness.prompts.routine_builder import RoutinePromptBuilder
from src.agents.wellness.prompts.wellness_coach import WellnessCoachPromptBuilder
from src.agents.wellness.reasoning import ReActEngine, ReActTrace
from src.database.repositories.routine_repository import RoutineRepository
from src.memory import MemoryStore, Message
from src.services.llm import LLMService
from src.services.user_data import UserDataService
from src.tools import Tool, ToolResult

logger = logging.getLogger(__name__)


class _DefaultUserDataService:
    """Servicio por defecto de datos de usuario para inicialización sin BD."""

    async def get_user_data(self, user_id: int):
        from src.services.user_data import UserData

        uid = int(user_id) if str(user_id).isdigit() else 1
        return UserData(
            user_id=uid,
            profile={"name": "Adulto Mayor", "age": 70, "city": "Maracaibo"},
            health_profile={"pathologies": []},
            preferences={},
            safe_exercises=[],
        )


class WellnessCoachAgent(WellnessAgent):
    """Agente conversacional especializado en bienestar para adultos mayores.

    Usa patrón ReAct para razonar sobre mensajes del usuario y ejecutar
    herramientas cuando sea necesario antes de generar una respuesta.

    Precondiciones:
        - LLM configurado (Ollama/Gemini/OpenRouter).
        - Base de datos disponible para tools de consulta.
        - Memoria PostgreSQL para persistencia de conversaciones.

    Efectos secundarios:
        - Ejecuta herramientas que pueden consultar o modificar BD.
        - Persiste mensajes en memory_store.
    """

    def __init__(
        self,
        llm: LLMService | None = None,
        user_data: UserDataService | None = None,
        tools: list[Tool] | None = None,
        memory_store: MemoryStore | None = None,
        config: WellnessConfig | None = None,
        routine_repo: RoutineRepository | None = None,
        prompt_builder: RoutinePromptBuilder | None = None,
    ) -> None:
        if llm is None:
            llm = LLMService()
        if user_data is None:
            user_data = _DefaultUserDataService()
        if tools is None:
            tools = []

        super().__init__(
            llm=llm,
            user_data=user_data,
            routine_repo=routine_repo,
            prompt_builder=prompt_builder,
            config=config,
        )
        self._tools = tools
        self._memory = memory_store
        self._prompt_builder = WellnessCoachPromptBuilder()
        self._react_engine = ReActEngine(
            llm=llm,
            tools=tools,
            max_iterations=self._config.max_react_iterations,
            tool_failure_threshold=self._config.tool_failure_threshold,
        )


    async def chat(self, user_id: int | str, message: str) -> str:
        """Procesa un mensaje del usuario y retorna una respuesta en texto plano.

        Args:
            user_id: ID del usuario (int o str).
            message: Mensaje del usuario.

        Returns:
            Respuesta del coach en texto plano.
        """
        answer, _ = await self.chat_with_trace(user_id, message)
        return answer

    async def chat_with_trace(
        self, user_id: int | str, message: str
    ) -> tuple[str, ReActTrace]:
        """Procesa un mensaje del usuario y retorna tanto la respuesta como la traza ReAct.

        Flujo:
            1. Obtener historial conversacional desde MemoryStore.
            2. Construir prompt con perfil + historial.
            3. Ejecutar ciclo ReAct iterativo (Thought -> Action -> Observation).
            4. Persistir mensajes de usuario y asistente en memoria.
            5. Retornar tupla (respuesta_final, traza_react).
        """
        user_str_id = str(user_id)
        try:
            parsed_uid = int(str(user_id).split("-")[-1]) if "-" in str(user_id) else int(user_id)
        except (ValueError, TypeError):
            parsed_uid = 1

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
        user_profile = await self._get_user_profile(parsed_uid)

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

        return trace.final_answer, trace

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


_wellness_coach_agent_instance: WellnessCoachAgent | None = None


def get_wellness_coach_agent() -> WellnessCoachAgent:
    # Retorna una instancia singleton de WellnessCoachAgent
    global _wellness_coach_agent_instance
    if _wellness_coach_agent_instance is None:
        _wellness_coach_agent_instance = WellnessCoachAgent()
    return _wellness_coach_agent_instance


