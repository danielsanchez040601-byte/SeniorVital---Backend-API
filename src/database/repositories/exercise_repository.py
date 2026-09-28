"""Exercise repository — queries del catálogo de ejercicios."""

from sqlalchemy import select

from src.database.models import Exercise

from .base import BaseRepository


class ExerciseRepository(BaseRepository[Exercise]):
    """Repositorio de ejercicios del catálogo.

    Precondiciones: Sesión SQLAlchemy válida y abierta.
    Postcondiciones: Las queries retornan modelos ORM poblados.
    """

    async def get_all(self) -> list[Exercise]:
        """Retorna todos los ejercicios del catálogo."""
        stmt = select(Exercise)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_level(self, level: int) -> list[Exercise]:
        """Retorna ejercicios de un nivel específico (1-4)."""
        stmt = select(Exercise).where(Exercise.level == level)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
