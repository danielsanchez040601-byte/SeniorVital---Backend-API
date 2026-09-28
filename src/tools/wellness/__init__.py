"""Wellness tools — herramientas para el Wellness Coach Agent 2.0."""

from .exercise_catalog import ExerciseCatalogTool
from .generate_routine import GenerateRoutineTool
from .get_habits import GetHabitsTool
from .log_habit import LogHabitTool
from .get_progress import GetProgressTool
from .get_routine import GetRoutineTool
from .rag_search import RAGSearchTool
from .safety_check import SafetyCheckTool

WELLNESS_TOOLS = [
    ExerciseCatalogTool,
    GenerateRoutineTool,
    GetHabitsTool,
    LogHabitTool,
    GetProgressTool,
    GetRoutineTool,
    RAGSearchTool,
    SafetyCheckTool,
]

__all__ = [
    "ExerciseCatalogTool",
    "GenerateRoutineTool",
    "GetHabitsTool",
    "LogHabitTool",
    "GetProgressTool",
    "GetRoutineTool",
    "RAGSearchTool",
    "SafetyCheckTool",
    "WELLNESS_TOOLS",
]
