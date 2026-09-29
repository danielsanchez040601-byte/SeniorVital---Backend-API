"""Generic base repository with CRUD operations."""

from typing import Generic, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Repositorio base con operaciones CRUD genéricas.

    Attributes:
        _session: Sesión async de SQLAlchemy.
        _model: Modelo ORM a operar.
    """

    def __init__(self, session: AsyncSession, model: Type[T]) -> None:
        self._session = session
        self._model = model

    async def get_by_id(self, id: int) -> T | None:
        """Retorna una entidad por su ID, o None si no existe."""
        return await self._session.get(self._model, id)

    async def add(self, entity: T) -> T:
        """Agrega una entidad y hace flush para obtener el ID."""
        self._session.add(entity)
        await self._session.flush()
        return entity

    async def add_all(self, entities: list[T]) -> list[T]:
        """Agrega múltiples entidades en lote."""
        for e in entities:
            self._session.add(e)
        await self._session.flush()
        return entities

    async def delete(self, entity: T) -> None:
        """Elimina una entidad."""
        await self._session.delete(entity)
        await self._session.flush()

    async def exists(self, id: int) -> bool:
        """Retorna True si la entidad con el ID dado existe."""
        stmt = select(self._model.id).where(self._model.id == id).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None
