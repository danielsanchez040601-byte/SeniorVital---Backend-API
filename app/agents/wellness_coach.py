"""
Módulo de compatibilidad y redirección hacia la arquitectura canónica.
Cualquier llamada a app.agents.wellness_coach se redirige formalmente a
src.agents.wellness.coach.WellnessCoachAgent.
"""
import time
from typing import Dict, Any, Optional
from src.agents.wellness.coach import WellnessCoachAgent, get_wellness_coach_agent
from src.agents.wellness.agent import WellnessAgent

class LegacyWellnessCoachProxy(WellnessCoachAgent):
    """Proxy de compatibilidad para interfaces de orquestación legacy."""

    async def execute_react_cycle(self, user_id: str, query: str) -> Dict[str, Any]:
        start_t = time.time()
        response, trace = await self.chat_with_trace(user_id=user_id, message=query)
        elapsed = round(time.time() - start_t, 2)
        return {
            "response": response,
            "user_id": user_id,
            "elapsed_time": elapsed,
            "reasoning_trace": trace.thought if trace else "ReAct cycle executed",
            "is_safe": True
        }

wellness_coach_agent = LegacyWellnessCoachProxy()
wellness_agent = wellness_coach_agent

__all__ = ["WellnessCoachAgent", "WellnessAgent", "wellness_coach_agent", "wellness_agent"]
