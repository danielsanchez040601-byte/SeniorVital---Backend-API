"""WellnessCoachAgent Adapter — adapta WellnessCoachAgent al Agent Protocol.

Permite que WellnessCoachAgent sea registrado en el OrchestratorAgent
sin modificar su código original. Implementa el Agent Protocol de
src/orchestration/agent_protocol.py.
"""

from __future__ import annotations

import logging
from typing import Any

from src.agents.wellness.coach import WellnessCoachAgent
from src.orchestration.agent_protocol import (
    AgentRequest,
    AgentResponse,
)

logger = logging.getLogger(__name__)


class WellnessCoachAgentAdapter:
    """Adapter: WellnessCoachAgent → Agent Protocol.

    Wraps WellnessCoachAgent.chat() para que cumpla el contrato
    de Agent.handle(). Permite registro en OrchestratorAgent.

    Precondiciones:
        - WellnessCoachAgent inicializado con LLM, tools, y memoria.

    Postcondiciones:
        - handle() retorna AgentResponse con safety_level.
        - can_handle() retorna True (agente general).

    Efectos secundarios:
        - Hereda los del WellnessCoachAgent subyacente.
    """

    name = "wellness_coach"
    domain = "general"
    description = "Agente conversacional general de bienestar para adultos mayores"

    def __init__(self, coach: WellnessCoachAgent) -> None:
        self._coach = coach

    async def handle(self, request: AgentRequest) -> AgentResponse:
        """Convierte AgentRequest → WellnessCoachAgent.chat().

        Args:
            request: Solicitud con message, user_id, y contexto.

        Returns:
            AgentResponse con la respuesta del coach.
        """
        logger.info(
            f"WellnessCoachAgentAdapter handling: user={request.user_id}, "
            f"message={request.message[:80]}..."
        )

        try:
            response = await self._coach.chat(
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
            logger.error(f"WellnessCoachAgent failed: {e}")
            return AgentResponse(
                text=(
                    "Disculpa, no pude procesar tu solicitud en este momento. "
                    "¿Podrías reformularla?"
                ),
                safety_level="safe",
                tool_chain=[],
                metadata={"agent": self.name, "error": str(e)},
            )

    def can_handle(self, intent: str, confidence: float) -> bool:
        """El agente general acepta cualquier intención."""
        return True
