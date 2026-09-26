"""User repository — queries específicas de dominio para usuarios."""

from sqlalchemy import select

from src.database.models import Exercise, User

from .base import BaseRepository


class UserNotFoundError(Exception):
    """Se lanza cuando un usuario no existe en la BD."""

    def __init__(self, user_id: int) -> None:
        super().__init__(f"User not found: {user_id}")
        self.user_id = user_id


class UserRepository(BaseRepository[User]):
    """Repositorio de usuarios con queries específicas del dominio.

    Precondiciones: Sesión SQLAlchemy válida y abierta.
    Postcondiciones: Las queries retornan modelos ORM poblados.
    """

    async def get_by_email(self, email: str) -> User | None:
        """Retorna usuario por email, o None si no existe."""
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_safe_exercises(self, user_id: int) -> tuple[User, list[Exercise]]:
        """Obtiene usuario + ejercicios seguros (sin contraindicaciones).

        Precondiciones: user_id debe existir en la BD.
        Postcondiciones: retorna tupla (user, safe_exercises).
        Excepciones: UserNotFoundError si el usuario no existe.

        Args:
            user_id: ID del usuario a buscar.

        Returns:
            Tupla (User, list[Exercise]) con ejercicios sin contraindicaciones.

        Raises:
            UserNotFoundError: Si no hay usuario con ese ID.
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)

        restrictions = set(
            user.health_profile.get("medical_restrictions",
                                     user.profile.get("medical_restrictions", []))
        )

        stmt = select(Exercise)
        result = await self._session.execute(stmt)
        all_exercises = result.scalars().all()

        safe = [e for e in all_exercises if not self._has_contraindication(e, restrictions)]
        return user, safe

    @staticmethod
    def _has_contraindication(exercise: Exercise, restrictions: set) -> bool:
        """Retorna True si el ejercicio tiene contraindicaciones que overlap con restricciones."""
        if not exercise.contraindications:
            return False
        contra = {x.strip() for x in exercise.contraindications.split(",") if x.strip()}
        return bool(contra & restrictions)
