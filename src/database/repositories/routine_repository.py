"""Routine repository — CRUD de rutinas generadas."""

from datetime import date

from sqlalchemy import select

from src.database.models import Routine

from .base import BaseRepository


class RoutineRepository(BaseRepository[Routine]):
    """Repositorio de rutinas diarias generadas por IA.

    Precondiciones: Sesión SQLAlchemy válida y abierta.
    Postcondiciones: Las queries retornan modelos ORM poblados.
    """

    async def get_active_by_user_and_date(
        self, user_id: int, target_date: date
    ) -> Routine | None:
        """Retorna la rutina activa de un usuario para una fecha dada.

        Args:
            user_id: ID del usuario.
            target_date: Fecha a buscar.

        Returns:
            Routine activa o None si no existe.
        """
        stmt = (
            select(Routine)
            .where(
                Routine.user_id == user_id,
                Routine.date == target_date,
                Routine.active.is_(True),
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: int,
        target_date: date,
        exercises: list[dict],
        warmup: list[dict] | str,
        generated_by: str = "ollama",
    ) -> Routine:
        """Crea y persiste una nueva rutina.

        Args:
            user_id: ID del usuario.
            target_date: Fecha programada.
            exercises: Lista de ejercicios (JSON).
            warmup: Calentamiento (lista o string).
            generated_by: Origen de la rutina (ollama | fallback).

        Returns:
            Routine creada con ID poblado.
        """
        import json

        routine = Routine(
            user_id=user_id,
            date=target_date,
            exercises=json.dumps(exercises) if isinstance(exercises, list) else exercises,
            warmup=json.dumps(warmup) if isinstance(warmup, list) else warmup,
            generated_by=generated_by,
        )
        return await self.add(routine)
