"""User data service — orquesta repositorios para obtener datos de usuario."""

from dataclasses import dataclass

from src.database.models import Exercise, User
from src.database.repositories.exercise_repository import ExerciseRepository
from src.database.repositories.user_repository import (
    UserRepository,
    UserNotFoundError,
)


@dataclass
class UserData:
    """Datos completos de usuario para generación de rutinas.

    Attributes:
        user_id: ID único del usuario.
        profile: Perfil adicional del usuario (JSONB).
        health_profile: Perfil de salud (edad, peso, restricciones).
        preferences: Preferencias del usuario (favoritos, evitar).
        safe_exercises: Lista de ejercicios sin contraindicaciones.
    """

    user_id: int
    profile: dict
    health_profile: dict
    preferences: dict
    safe_exercises: list[dict]


class UserDataService:
    """Orquesta repositorios para obtener datos completos de usuario.

    Precondiciones: Sesión SQLAlchemy válida.
    Postcondiciones: UserData con todos los campos poblados.
    Excepciones: UserNotFoundError si user_id no existe.
    """

    def __init__(
        self, user_repo: UserRepository, exercise_repo: ExerciseRepository
    ) -> None:
        self._user_repo = user_repo
        self._exercise_repo = exercise_repo

    async def get_user_data(self, user_id: int) -> UserData:
        """Obtiene datos completos de usuario para generación de rutinas.

        Args:
            user_id: ID del usuario a buscar.

        Returns:
            UserData con perfil, ejercicios y preferencias.

        Raises:
            UserNotFoundError: Si no hay usuario con ese ID.
        """
        user, safe_exercises = await self._user_repo.get_with_safe_exercises(user_id)
        return UserData(
            user_id=user.id,
            profile=user.profile or {},
            health_profile=user.health_profile or {},
            preferences=user.preferences or {},
            safe_exercises=[self._exercise_to_dict(e) for e in safe_exercises],
        )

    @staticmethod
    def _exercise_to_dict(exercise: Exercise) -> dict:
        """Convierte un Exercise ORM a dict para el prompt builder."""
        return {
            "id": exercise.id,
            "name": exercise.name,
            "description": exercise.description or "",
            "level": exercise.level,
            "duration_min": 5,  # Default; el prompt builder puede sobreescribir
            "contraindications": exercise.contraindications or "",
        }
