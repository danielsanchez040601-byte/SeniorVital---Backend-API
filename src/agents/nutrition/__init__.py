"""NutritionAgent — agente especializado en nutrición para adultos mayores."""

from src.agents.nutrition.agent import NutritionAgent
from src.agents.nutrition.adapter import NutritionAgentAdapter
from src.agents.nutrition.prompts import NutritionPromptBuilder
from src.agents.nutrition.tools import NutritionCalculatorTool, ClinicalDietaryCheckTool

__all__ = [
    "NutritionAgent",
    "NutritionAgentAdapter",
    "NutritionPromptBuilder",
    "NutritionCalculatorTool",
    "ClinicalDietaryCheckTool",
]
