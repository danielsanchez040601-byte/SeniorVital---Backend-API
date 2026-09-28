"""PostgreSQL implementation of the MemoryStore protocol.

Stores conversational history in the conversation_history table.
Uses the shared asyncpg pool from seniorvital_shared.
"""

import json
import logging
from datetime import datetime, timezone

import asyncpg

from src.memory import Message

logger = logging.getLogger(__name__)


class PostgresMemoryStore:
    """Implementación PostgreSQL del MemoryStore protocol.

    Precondiciones:
        - asyncpg Pool inicializado y conectado a PostgreSQL.
        - Tabla conversation_history creada (migración S2-03).

    Postcondiciones:
        - get_history retorna mensajes ordenados cronológicamente.
        - add_message persiste el mensaje de forma duradera.
        - clear_history elimina TODO el historial del usuario.

    Efectos secundarios:
        - add_message INSERT en conversation_history.
        - clear_history DELETE en conversation_history (destructivo).
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get_history(self, user_id: str, limit: int = 20) -> list[Message]:
        """Recupera los últimos N mensajes del usuario.

        Args:
            user_id: Identificador único del usuario.
            limit: Número máximo de mensajes a retornar (default: 20).

        Returns:
            Lista de mensajes ordenados cronológicamente (más antiguo al final).
            Retorna lista vacía si no hay historial.

        Raises:
            ValueError: Si limit es negativo.
        """
        if limit < 0:
            raise ValueError("limit must be non-negative")

        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    """SELECT role, content, metadata, created_at
                       FROM conversation_history
                       WHERE user_id = $1
                       ORDER BY created_at DESC
                       LIMIT $2""",
                    int(user_id), limit,
                )
        except Exception as e:
            logger.error(f"Failed to get history for user {user_id}: {e}")
            raise

        # Revertir para orden cronológico (más antiguo primero)
        messages = []
        for r in reversed(rows):
            raw_meta = r["metadata"]
            if isinstance(raw_meta, str):
                meta = json.loads(raw_meta) if raw_meta else {}
            elif raw_meta:
                meta = dict(raw_meta)
            else:
                meta = {}
            messages.append(Message(
                role=r["role"],
                content=r["content"],
                timestamp=r["created_at"].isoformat(),
                metadata=meta,
            ))
        return messages

    async def add_message(self, user_id: str, message: Message) -> None:
        """Inserta un mensaje en el historial.

        Args:
            user_id: Identificador único del usuario.
            message: Mensaje a almacenar.

        Raises:
            ValueError: Si message.role no es un rol válido.
            MemoryError: Si falla la persistencia en la BD.
        """
        if message.role not in ("user", "assistant", "system"):
            raise ValueError(f"Invalid role: {message.role}")

        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO conversation_history (user_id, role, content, metadata)
                       VALUES ($1, $2, $3, $4)""",
                    int(user_id),
                    message.role,
                    message.content,
                    json.dumps(message.metadata) if message.metadata else "{}",
                )
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to add message for user {user_id}: {e}")
            raise MemoryError(f"Failed to persist message: {e}") from e

    async def clear_history(self, user_id: str) -> None:
        """Elimina todo el historial de un usuario.

        Esta operación es destructiva e irreversible.

        Args:
            user_id: Identificador único del usuario.

        Raises:
            MemoryError: Si falla la eliminación en la BD.
        """
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM conversation_history WHERE user_id = $1",
                    int(user_id),
                )
        except Exception as e:
            logger.error(f"Failed to clear history for user {user_id}: {e}")
            raise MemoryError(f"Failed to clear history: {e}") from e
