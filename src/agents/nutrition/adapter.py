"""NutritionAgent Adapter — adapta NutritionAgent al Agent Protocol.

Permite que NutritionAgent sea registrado en el OrchestratorAgent
sin modificar su código original. Implementa el Agent Protocol de
src/orchestration/agent_protocol.py.
"""

from __future__ import annotations

import logging

from src.agents.nutrition.agent import NutritionAgent
from src.orchestration.agent_protocol import (
    AgentRequest,
    AgentResponse,
)

logger = logging.getLogger(__name__)


class NutritionAgentAdapter:
    """Adapter: NutritionAgent → Agent Protocol.

    Wraps NutritionAgent.chat() para que cumpla el contrato
    de Agent.handle(). Permite registro en OrchestratorAgent.

    Precondiciones:
        - NutritionAgent inicializado con LLM, tools, y memoria.

    Postcondiciones:
        - handle() retorna AgentResponse con safety_level.
        - can_handle() retorna True solo para dominio nutrition.

    Efectos secundarios:
        - Hereda los del NutritionAgent subyacente.
    """

    name = "nutrition"
    domain = "nutrition"
    description = "Agente especializado en nutrición y dietas para adultos mayores"

    def __init__(self, agent: NutritionAgent) -> None:
        self._agent = agent

    async def handle(self, request: AgentRequest) -> AgentResponse:
        """Convierte AgentRequest → NutritionAgent.chat().

        Args:
            request: Solicitud con message, user_id, y contexto.

        Returns:
            AgentResponse con la respuesta del agente de nutrición.
        """
        logger.info(
            f"NutritionAgentAdapter handling: user={request.user_id}, "
            f"message={request.message[:80]}..."
        )

        try:
            response = await self._agent.chat(
                user_id=request.user_id,
                message=request.message,
            )

            return AgentResponse(
                text=response,
                safety_level="safe",
                tool_chain=[],
                metadata={"agent": self.name, "domain": self.domain},
            )

        except Exception as e:
            logger.error(f"NutritionAgent failed: {e}")
            return AgentResponse(
                text=(
                    "Disculpa, no pude procesar tu solicitud de nutrición en este momento. "
                    "¿Podrías reformularla?"
                ),
                safety_level="safe",
                tool_chain=[],
                metadata={"agent": self.name, "error": str(e)},
            )

    def can_handle(self, intent: str, confidence: float) -> bool:
        """Solo acepta intenciones del dominio nutrition."""
        return intent == self.domain and confidence >= 0.5
