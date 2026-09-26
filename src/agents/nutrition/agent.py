"""NutritionAgent — agente especializado en nutrición para adultos mayores.

Herramientas:
- rag_search: Busca información nutricional en la base de conocimiento.
- safety_check: Verifica si la recomendación es segura para el usuario.

Reutiliza:
- ReActEngine para tool calling.
- MemoryStore para persistencia conversacional.
"""

import logging
from typing import Any

from src.agents.nutrition.prompts import NutritionPromptBuilder
from src.agents.wellness.config import WellnessConfig
from src.agents.wellness.reasoning import ReActEngine
from src.memory import MemoryStore, Message
from src.orchestration.agent_protocol import AgentRequest
from src.services.llm import LLMService
from src.services.user_data import UserDataService
from src.tools import Tool

logger = logging.getLogger(__name__)


class NutritionAgent:
    """Agente especializado en nutrición con tool calling y ReAct.

    Precondiciones:
        - LLMService con conexión a Ollama activa.
        - Herramientas inyectadas (rag_search, safety_check).
        - MemoryStore implementado (puede ser None para modo sin memoria).

    Postcondiciones:
        - Retorna respuesta personalizada sobre nutrición.
        - Historial conversacional actualizado (si memory_store != None).

    Efectos secundarios:
        - Ejecuta herramientas que pueden consultar la BD (rag_search).
    """

    def __init__(
        self,
        llm: LLMService,
        user_data: UserDataService,
        tools: list[Tool],
        memory_store: MemoryStore | None = None,
        config: WellnessConfig | None = None,
        firestore_client: Any | None = None,
        bigquery_client: Any | None = None,
    ) -> None:
        self._llm = llm
        self._user_data = user_data
        self._tools = tools
        self._memory = memory_store
        self._config = config or WellnessConfig()
        self._firestore = firestore_client
        self._bigquery = bigquery_client
        self._prompt_builder = NutritionPromptBuilder()
        self._react_engine = ReActEngine(
            llm=llm,
            tools=tools,
            max_iterations=self._config.max_react_iterations,
            tool_failure_threshold=self._config.tool_failure_threshold,
        )

    async def chat(self, user_id: int, message: str) -> str:
        """Procesa un mensaje del usuario y retorna una respuesta sobre nutrición.

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
            Respuesta del asistente de nutrición en texto plano.
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
        trace =         await self._react_engine.run(system_prompt, user_prompt)

        logger.info(
            f"NutritionAgent trace: {trace.iterations} iterations, "
            f"{len(trace.steps)} steps, "
            f"final_answer={trace.final_answer[:100]}..."
        )

        # 4.1 Fallback si la respuesta está vacía
        if not trace.final_answer or not trace.final_answer.strip():
            trace.final_answer = (
                "Disculpa, no pude procesar tu solicitud de nutrición en este momento. "
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

    async def process(self, request: AgentRequest) -> str:
        """Procesa una solicitud (entry point de la tarea S3-03).

        Delega en chat() con los datos del AgentRequest, manteniendo
        una única fuente de lógica conversacional.

        Args:
            request: Solicitud con message y user_id.

        Returns:
            Respuesta del agente de nutrición en texto plano.
        """
        return await self.chat(
            user_id=request.user_id,
            message=request.message,
        )

    async def _get_user_profile(self, user_id: int) -> dict:
        """Obtiene el perfil del usuario para el prompt.

        Si firestore_client está disponible, enriquece con hábitos
        (agua, sueño) que afectan las recomendaciones nutricionales.

        Returns:
            Dict con name, age, health, restrictions, y datos adicionales.
        """
        try:
            data = await self._user_data.get_user_data(user_id)
            profile = {
                "name": data.profile.get("name", ""),
                "age": data.profile.get("age", ""),
                "health": data.health_profile,
                "restrictions": data.preferences.get("dietary_restrictions", []),
            }
        except Exception as e:
            logger.warning(f"Failed to get user profile for {user_id}: {e}")
            profile = {"user_id": user_id}

        # Enrich with Firestore data if available
        if self._firestore:
            try:
                habits = await self._firestore.get_user_habits(user_id, days=7)
                if habits:
                    profile["recent_habits"] = habits
                health = await self._firestore.get_user_health(user_id)
                if health and "weight" in health:
                    profile["weight"] = health["weight"]
                if health and "height" in health:
                    profile["height"] = health["height"]
            except Exception as e:
                logger.warning(f"Failed to enrich profile from Firestore for {user_id}: {e}")

        # Enrich with BigQuery analytics if available
        if self._bigquery:
            try:
                weekly = await self._bigquery.get_weekly_progress(user_id, weeks=4)
                if weekly:
                    profile["weekly_insights"] = weekly[:3]
            except Exception as e:
                logger.warning(f"Failed to enrich profile from BigQuery for {user_id}: {e}")

        return profile
