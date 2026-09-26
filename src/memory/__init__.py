"""Memory module — protocols y implementaciones de memoria conversacional.

Este módulo define las interfaces (protocols) y implementaciones concretas
para sistemas de memoria conversacional.

Ejemplo de uso::

    from src.memory import MemoryStore, Message, PostgresMemoryStore

    store: MemoryStore = PostgresMemoryStore(pool)
    await store.add_message("1", Message(role="user", content="Hola", timestamp="..."))
    history = await store.get_history("1", limit=5)
"""

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class Message:
    """Representa un mensaje en la conversación.

    Attributes:
        role: Rol del mensaje. Valores válidos: "user", "assistant", "system".
        content: Contenido del mensaje en texto plano.
        timestamp: Timestamp UTC del mensaje en formato ISO 8601.
        metadata: Metadatos opcionales (tool calls, sources, etc.).
    """

    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: str  # ISO 8601
    metadata: dict = field(default_factory=dict)


@runtime_checkable
class MemoryStore(Protocol):
    """Contrato para almacenes de memoria conversacional.

    Precondiciones:
        - La instancia debe estar inicializada y conectada a su backend
          (Redis, archivos, base de datos, etc.).
        - Las operaciones son atómicas — falla completa si hay error.

    Postcondiciones:
        - get_history retorna mensajes ordenados cronológicamente.
        - add_message persiste el mensaje de forma duradera.
        - clear_history elimina TODO el historial del usuario.

    Efectos secundarios:
        - add_message incrementa el tamaño del historial.
        - clear_history es destructivo e irreversible.

    Excepciones:
        - ValueError: Si los parámetros de entrada son inválidos.
        - MemoryError: Si falla la operación de persistencia del backend.
    """

    async def get_history(self, user_id: str, limit: int = 20) -> list[Message]:
        """Retorna el historial reciente de conversación para un usuario.

        Args:
            user_id: Identificador único del usuario.
            limit: Número máximo de mensajes a retornar (default: 20).

        Returns:
            Lista de mensajes ordenados cronológicamente (más reciente al final).
            Retorna lista vacía si no hay historial.

        Raises:
            ValueError: Si limit es negativo.
        """
        ...

    async def add_message(self, user_id: str, message: Message) -> None:
        """Agrega un mensaje al historial del usuario.

        Args:
            user_id: Identificador único del usuario.
            message: Mensaje a almacenar.

        Raises:
            ValueError: Si message.role no es un rol válido ("user", "assistant", "system").
            MemoryError: Si falla la persistencia en el backend.
        """
        ...

    async def clear_history(self, user_id: str) -> None:
        """Elimina todo el historial de un usuario.

        Esta operación es destructiva e irreversible.

        Args:
            user_id: Identificador único del usuario.

        Raises:
            MemoryError: Si falla la eliminación en el backend.
        """
        ...
