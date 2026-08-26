"""Tests de aceptación para el servicio de tracking de ejercicios.

Cubre registro individual, detección de fatiga alta y registro por lote.
"""

import pytest
import json
from httpx import AsyncClient, ASGITransport
from .conftest import load_service_app
from seniorvital_shared import get_pool

app = load_service_app("tracking-service")


@pytest.fixture
async def client():
    """Fixture que proporciona un cliente HTTP asíncrono contra la app FastAPI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def seed_users():
    """Crea 3 usuarios senior en BD para usar en tests de tracking."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = []
        for i in range(1, 4):
            row = await conn.fetchrow(
                "INSERT INTO users (email, role, profile, password) VALUES ($1, $2, $3, $4) RETURNING id",
                f"tracking_user_{i}@test.com",
                "senior",
                json.dumps({}),
                "pw",
            )
            rows.append(str(row["id"]))
    return rows


@pytest.mark.asyncio
async def test_record_exercise(client, seed_users):
    user_id = seed_users[0]
    resp = await client.post("/tracking/record", json={
        "user_id": user_id,
        "exercise_id": "ex1",
        "sets": 3,
        "reps": 10,
        "rpe": 5,
    })
    assert resp.status_code == 200
    assert "id" in resp.json()


@pytest.mark.asyncio
async def test_record_high_fatigue(client, seed_users):
    user_id = seed_users[1]
    resp = await client.post("/tracking/record", json={
        "user_id": user_id,
        "exercise_id": "ex2",
        "sets": 3,
        "reps": 10,
        "rpe": 9,
    })
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_batch_record(client, seed_users):
    user_id = seed_users[2]
    resp = await client.post("/tracking/batch", json={
        "entries": [
            {
                "user_id": user_id,
                "exercise_id": "ex3",
                "sets": 2,
                "reps": 8,
                "rpe": 4,
            },
            {
                "user_id": user_id,
                "exercise_id": "ex4",
                "sets": 3,
                "reps": 12,
                "rpe": 6,
            },
        ]
    })
    assert resp.status_code == 200
    assert resp.json()["count"] == 2
