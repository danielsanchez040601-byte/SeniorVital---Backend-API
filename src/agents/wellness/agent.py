"""Wellness Agent — orquestador principal.

Extrae la lógica de negocio de routines-ai-service/main.py
en una clase testable sin dependencia HTTP.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime

from src.agents.wellness.config import WellnessConfig
from src.agents.wellness.prompts.routine_builder import RoutinePromptBuilder
from src.database.repositories.routine_repository import RoutineRepository
from src.services.llm import LLMService, LLMConnectionError, LLMTimeoutError
from src.services.user_data import UserData, UserDataService


@dataclass
class RoutineResult:
    """Resultado de una operación de rutina.

    Attributes:
        id: ID de la rutina en BD (None si no se guardó).
        user_id: ID del usuario.
        scheduled_date: Fecha programada (ISO 8601).
        exercises: Lista de ejercicios formateados.
        warmup: Lista de ejercicios de calentamiento.
        generated_at: Timestamp de generación (ISO 8601).
        generated_by: Origen (ollama | fallback).
        llm_available: Si el LLM respondió correctamente.
        llm_model: Nombre del modelo usado.
        llm_error: Mensaje de error si el LLM falló.
    """

    id: str | None = None
    user_id: str = ""
    scheduled_date: str = ""
    exercises: list[dict] = field(default_factory=list)
    warmup: list[dict] = field(default_factory=list)
    generated_at: str = ""
    generated_by: str = "ollama"
    llm_available: bool = True
    llm_model: str | None = None
    llm_error: str | None = None

    def to_dict(self) -> dict:
        """Serializa a dict para respuesta HTTP."""
        return {k: v for k, v in self.__dict__.items() if v is not None}


# -- Fallback routine (same as original) --
DEFAULT_ROUTINE = {
    "exercises": [
        {"name": "Caminata ligera", "sets": 1, "reps": 10, "rest_duration_sec": 30,
         "description": "Camina a paso suave", "exercise_id": 0, "duration_min": 5},
        {"name": "Estiramiento de brazos", "sets": 2, "reps": 8, "rest_duration_sec": 45,
         "description": "Estira los brazos hacia arriba", "exercise_id": 0, "duration_min": 3},
        {"name": "Respiración profunda", "sets": 1, "reps": 5, "rest_duration_sec": 20,
         "description": "Inhala y exhala profundamente", "exercise_id": 0, "duration_min": 2},
    ],
    "warmup": [
        {"name": "Rotación de cuello", "sets": 1, "reps": 5, "duration_min": 1}
    ],
}


def _clean_llm_response(response_text: str) -> str:
    """Limpia la respuesta del LLM para extraer JSON válido.

    Extraído de routines-ai-service/main.py _clean_ollama_response().
    """
    match = re.search(r"```(?:json)?\s*(.+?)\s*```", response_text, re.DOTALL)
    if match:
        response_text = match.group(1)
    response_text = response_text.strip()
    response_text = re.sub(r"//.*?$", "", response_text, flags=re.MULTILINE)
    response_text = re.sub(r",\s*([}\]])", r"\1", response_text)
    return response_text


def _format_exercises(exercises: list) -> list[dict]:
    """Convierte ejercicios del formato BD/LLM al formato del frontend.

    Extraído de routines-ai-service/main.py map_exercises().
    """
    result = []
    for i, ex in enumerate(exercises):
        if isinstance(ex, str):
            try:
                ex = json.loads(ex)
            except json.JSONDecodeError:
                ex = {}
        result.append({
            "exercise_id": ex.get("exercise_id", 0),
            "name": ex.get("name", ""),
            "description": ex.get("description", ""),
            "video_url": ex.get("video_url", ""),
            "sets": ex.get("sets", 1),
            "reps_per_set": ex.get("reps_per_set") or ex.get("reps") or 10,
            "rest_duration_sec": ex.get("rest_duration_sec") or (ex.get("duration_min") or 1) * 60,
            "progression_level_used": ex.get("progression_level_used", 1),
            "order_number": ex.get("order_number", i + 1),
        })
    return result


class WellnessAgent:
    """Orquestador del agente de bienestar.

    Separa la lógica de negocio de las capas HTTP y persistencia.

    Precondiciones: LLMService y UserDataService inicializados.
    Postcondiciones: RoutineResult con rutina generada o existente.
    Excepciones: UserNotFoundError, LLMError (con fallback a rutina por defecto).
    """

    def __init__(
        self,
        llm: LLMService,
        user_data: UserDataService,
        routine_repo: RoutineRepository,
        prompt_builder: RoutinePromptBuilder | None = None,
        config: WellnessConfig | None = None,
    ) -> None:
        self._llm = llm
        self._user_data = user_data
        self._routine_repo = routine_repo
        self._prompts = prompt_builder or RoutinePromptBuilder()
        self._config = config or WellnessConfig()

    async def generate_routine(
        self, user_id: int, force: bool = False
    ) -> RoutineResult:
        """Genera rutina para el día de hoy.

        Si ya existe una rutina activa y force=False, la retorna sin regenerar.
        Si el LLM falla, usa una rutina por defecto como fallback.

        Args:
            user_id: ID del usuario.
            force: Si True, regenera aunque ya exista una rutina hoy.

        Returns:
            RoutineResult con la rutina generada o existente.
        """
        today = date.today()

        # 1. Verificar si ya existe rutina para hoy
        if not force:
            existing = await self._routine_repo.get_active_by_user_and_date(user_id, today)
            if existing:
                exercises = (
                    json.loads(existing.exercises)
                    if isinstance(existing.exercises, str)
                    else (existing.exercises or [])
                )
                warmup = (
                    json.loads(existing.warmup)
                    if isinstance(existing.warmup, str)
                    else (existing.warmup or [])
                )
                return RoutineResult(
                    id=str(existing.id),
                    user_id=str(user_id),
                    scheduled_date=today.isoformat(),
                    exercises=_format_exercises(exercises),
                    warmup=warmup,
                    generated_at=(
                        existing.created_at.isoformat()
                        if existing.created_at
                        else today.isoformat()
                    ),
                    generated_by=existing.generated_by or "ollama",
                    llm_available=True,
                    llm_model="cached",
                )

        # 2. Obtener datos del usuario
        user_data = await self._user_data.get_user_data(user_id)

        # 3. Generar con LLM (con fallback)
        llm_available = True
        llm_error = None
        routine_data = None

        try:
            prompt = self._prompts.build(
                user_data.profile,
                user_data.health_profile,
                user_data.preferences,
                user_data.safe_exercises,
            )
            raw_response = await self._llm.generate(prompt, format_json=True)
            parsed = json.loads(_clean_llm_response(raw_response))
            routine_data = {
                "exercises": parsed.get("exercises", []),
                "warmup": parsed.get("warmup", []),
            }
        except LLMTimeoutError as e:
            llm_available = False
            llm_error = str(e)
            routine_data = DEFAULT_ROUTINE
        except LLMConnectionError as e:
            llm_available = False
            llm_error = str(e)
            routine_data = DEFAULT_ROUTINE
        except Exception as e:
            llm_available = False
            llm_error = f"{type(e).__name__}: {e}"
            routine_data = DEFAULT_ROUTINE

        # 4. Guardar en BD
        saved = await self._routine_repo.create(
            user_id=user_id,
            target_date=today,
            exercises=routine_data.get("exercises", []),
            warmup=routine_data.get("warmup", []),
            generated_by="ollama" if llm_available else "fallback",
        )

        return RoutineResult(
            id=str(saved.id),
            user_id=str(user_id),
            scheduled_date=today.isoformat(),
            exercises=_format_exercises(routine_data.get("exercises", [])),
            warmup=routine_data.get("warmup", []),
            generated_at=(
                saved.created_at.isoformat() if saved.created_at else today.isoformat()
            ),
            generated_by="ollama" if llm_available else "fallback",
            llm_available=llm_available,
            llm_model=self._llm.model if llm_available else None,
            llm_error=llm_error,
        )

    async def get_today_routine(self, user_id: int) -> RoutineResult:
        """Obtiene la rutina activa del día de hoy.

        Args:
            user_id: ID del usuario.

        Returns:
            RoutineResult con la rutina existente.

        Raises:
            ValueError: Si no hay rutina para hoy.
        """
        today = date.today()
        routine = await self._routine_repo.get_active_by_user_and_date(user_id, today)
        if not routine:
            raise ValueError("No routine for today")

        exercises = (
            json.loads(routine.exercises)
            if isinstance(routine.exercises, str)
            else (routine.exercises or [])
        )
        warmup = (
            json.loads(routine.warmup)
            if isinstance(routine.warmup, str)
            else (routine.warmup or [])
        )
        return RoutineResult(
            id=str(routine.id),
            user_id=str(user_id),
            scheduled_date=today.isoformat(),
            exercises=_format_exercises(exercises),
            warmup=warmup,
            generated_at=(
                routine.created_at.isoformat()
                if routine.created_at
                else today.isoformat()
            ),
            generated_by=routine.generated_by or "ollama",
            llm_available=True,
            llm_model="cached",
        )
