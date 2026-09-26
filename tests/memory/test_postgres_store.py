"""Integration tests for PostgresMemoryStore — real PostgreSQL backend.

These tests require a running PostgreSQL instance with the conversation_history table.
They use the shared asyncpg pool from seniorvital_shared.
"""

import uuid
import pytest
from datetime import datetime, timezone

from src.memory import Message
from src.memory.postgres_store import PostgresMemoryStore


@pytest.fixture
async def pool():
    """Get the shared asyncpg pool (initialized by conftest auto_init_pool)."""
    from seniorvital_shared import get_pool
    return await get_pool()


@pytest.fixture
async def store(pool):
    """Create a PostgresMemoryStore with the shared pool."""
    return PostgresMemoryStore(pool)


@pytest.fixture
async def seed_user(pool):
    """Insert a test user and return the user_id. Uses unique email per test."""
    email = f"memory_{uuid.uuid4().hex[:8]}@test.com"
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO users (email, password, role, nombre_senior)
               VALUES ($1, 'hash', 'senior', 'TestUser')
               RETURNING id""",
            email,
        )
        return row["id"]


# ── Tests: add_message + get_history ──

@pytest.mark.asyncio
async def test_add_and_get_single_message(store, seed_user):
    """Un mensaje se persiste y se recupera correctamente."""
    uid = str(seed_user)
    msg = Message(role="user", content="Hola coach", timestamp=datetime.now(timezone.utc).isoformat())

    await store.add_message(uid, msg)
    history = await store.get_history(uid, limit=10)

    assert len(history) == 1
    assert history[0].role == "user"
    assert history[0].content == "Hola coach"


@pytest.mark.asyncio
async def test_get_history_chronological_order(store, seed_user):
    """Los mensajes se recuperan en orden cronológico (más antiguo primero)."""
    uid = str(seed_user)
    now = datetime.now(timezone.utc).isoformat()

    await store.add_message(uid, Message(role="user", content="Primero", timestamp=now))
    await store.add_message(uid, Message(role="assistant", content="Respuesta 1", timestamp=now))
    await store.add_message(uid, Message(role="user", content="Segundo", timestamp=now))
    await store.add_message(uid, Message(role="assistant", content="Respuesta 2", timestamp=now))

    history = await store.get_history(uid, limit=10)

    assert len(history) == 4
    assert history[0].content == "Primero"
    assert history[1].content == "Respuesta 1"
    assert history[2].content == "Segundo"
    assert history[3].content == "Respuesta 2"


@pytest.mark.asyncio
async def test_get_history_respects_limit(store, seed_user):
    """El parámetro limit controla cuántos mensajes se retornan."""
    uid = str(seed_user)
    now = datetime.now(timezone.utc).isoformat()

    for i in range(10):
        await store.add_message(uid, Message(role="user", content=f"Msg {i}", timestamp=now))

    history = await store.get_history(uid, limit=3)

    assert len(history) == 3
    # Los 3 más recientes
    assert history[0].content == "Msg 7"
    assert history[1].content == "Msg 8"
    assert history[2].content == "Msg 9"


@pytest.mark.asyncio
async def test_get_history_empty(store, seed_user):
    """Retorna lista vacía si no hay historial."""
    uid = str(seed_user)
    history = await store.get_history(uid, limit=10)
    assert history == []


@pytest.mark.asyncio
async def test_get_history_negative_limit_raises(store, seed_user):
    """Lanza ValueError si limit es negativo."""
    with pytest.raises(ValueError, match="non-negative"):
        await store.get_history(str(seed_user), limit=-1)


@pytest.mark.asyncio
async def test_add_message_invalid_role_raises(store, seed_user):
    """Lanza ValueError si el role no es válido."""
    msg = Message(role="invalid", content="Test", timestamp=datetime.now(timezone.utc).isoformat())
    with pytest.raises(ValueError, match="Invalid role"):
        await store.add_message(str(seed_user), msg)


# ── Tests: clear_history ──

@pytest.mark.asyncio
async def test_clear_history(store, seed_user):
    """clear_history elimina todos los mensajes del usuario."""
    uid = str(seed_user)
    now = datetime.now(timezone.utc).isoformat()

    await store.add_message(uid, Message(role="user", content="Msg 1", timestamp=now))
    await store.add_message(uid, Message(role="assistant", content="Reply 1", timestamp=now))

    assert len(await store.get_history(uid)) == 2

    await store.clear_history(uid)

    assert len(await store.get_history(uid)) == 0


@pytest.mark.asyncio
async def test_clear_history_does_not_affect_other_users(store, pool):
    """clear_history solo afecta al usuario especificado."""
    async with pool.acquire() as conn:
        r1 = await conn.fetchrow(
            "INSERT INTO users (email, password, role, nombre_senior) VALUES ($1, 'h', 'senior', 'U1') RETURNING id",
            f"u1_{uuid.uuid4().hex[:8]}@t.com",
        )
        r2 = await conn.fetchrow(
            "INSERT INTO users (email, password, role, nombre_senior) VALUES ($1, 'h', 'senior', 'U2') RETURNING id",
            f"u2_{uuid.uuid4().hex[:8]}@t.com",
        )

    now = datetime.now(timezone.utc).isoformat()
    await store.add_message(str(r1["id"]), Message(role="user", content="User1 msg", timestamp=now))
    await store.add_message(str(r2["id"]), Message(role="user", content="User2 msg", timestamp=now))

    await store.clear_history(str(r1["id"]))

    assert len(await store.get_history(str(r1["id"]))) == 0
    assert len(await store.get_history(str(r2["id"]))) == 1


# ── Tests: metadata ──

@pytest.mark.asyncio
async def test_message_metadata_persisted(store, seed_user):
    """El campo metadata se persiste y recupera correctamente."""
    uid = str(seed_user)
    msg = Message(
        role="user",
        content="Test metadata",
        timestamp=datetime.now(timezone.utc).isoformat(),
        metadata={"tool_call": "exercise_catalog", "sources": ["doc1"]},
    )

    await store.add_message(uid, msg)
    history = await store.get_history(uid, limit=1)

    assert history[0].metadata == {"tool_call": "exercise_catalog", "sources": ["doc1"]}


@pytest.mark.asyncio
async def test_message_empty_metadata(store, seed_user):
    """Metadata vacía se persiste como dict vacío."""
    uid = str(seed_user)
    msg = Message(role="user", content="No meta", timestamp=datetime.now(timezone.utc).isoformat())

    await store.add_message(uid, msg)
    history = await store.get_history(uid, limit=1)

    assert history[0].metadata == {}


# ── Tests: multi-user isolation ──

@pytest.mark.asyncio
async def test_users_are_isolated(store, pool):
    """Cada usuario tiene su propio historial."""
    async with pool.acquire() as conn:
        r1 = await conn.fetchrow(
            "INSERT INTO users (email, password, role, nombre_senior) VALUES ($1, 'h', 'senior', 'I1') RETURNING id",
            f"iso1_{uuid.uuid4().hex[:8]}@t.com",
        )
        r2 = await conn.fetchrow(
            "INSERT INTO users (email, password, role, nombre_senior) VALUES ($1, 'h', 'senior', 'I2') RETURNING id",
            f"iso2_{uuid.uuid4().hex[:8]}@t.com",
        )

    now = datetime.now(timezone.utc).isoformat()
    await store.add_message(str(r1["id"]), Message(role="user", content="Msg for I1", timestamp=now))
    await store.add_message(str(r2["id"]), Message(role="user", content="Msg for I2", timestamp=now))

    h1 = await store.get_history(str(r1["id"]))
    h2 = await store.get_history(str(r2["id"]))

    assert len(h1) == 1
    assert h1[0].content == "Msg for I1"
    assert len(h2) == 1
    assert h2[0].content == "Msg for I2"
