"""
Módulo de compatibilidad y redirección hacia la arquitectura canónica.
Cualquier llamada residual hacia app.agents.wellness_coach se redirige formalmente a
src.agents.wellness.coach.WellnessCoachAgent.
"""
from src.agents.wellness.coach import WellnessCoachAgent
from src.agents.wellness.agent import WellnessAgent

__all__ = ["WellnessCoachAgent", "WellnessAgent"]
