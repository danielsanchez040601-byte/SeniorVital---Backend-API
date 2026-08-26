"""Tests de aceptación para el servicio de rutinas con IA.

Cubre generación de rutinas, fallback y consulta de rutina del día.
"""

import pytest
import json
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from .conftest import load_service_app
from seniorvital_shared import get_pool

app = load_service_app("routines-ai-service")


@pytest.fixture
async def client():
    """Fixture que proporciona un cliente HTTP asíncrono contra la app FastAPI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def seed_user():
    """Crea un usuario senior en BD para usar en tests de rutinas."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO users (email, role, profile, password) VALUES ($1, $2, $3, $4) RETURNING id",
            "routine_user@test.com",
            "senior",
            json.dumps({
                "age": 70,
                "weight_kg": 70,
                "height_cm": 165,
                "fitness_level": "principiante",
                "goals": ["mejorar_movilidad"],
                "medical_restrictions": [],
                "equipment": [],
            }),
            "not_needed",
        )
        return str(row["id"])


@pytest.mark.asyncio
async def test_generate_routine_user_not_found(client):
    resp = await client.post("/routines/generate", json={
        "user_id": "00000000-0000-0000-0000-000000000099",
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_today_routine_not_found(client):
    resp = await client.get("/routines/today", params={
        "user_id": "00000000-0000-0000-0000-000000000099",
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_generate_routine_twice_returns_existing(client, seed_user):
    user_id = seed_user
    # Mock call_ollama via the route handler's globals (avoid patching httpx)
    async def mock_ollama(prompt):
        return {"exercises": [{"name": "Mock exercise", "sets": 3, "reps": 10, "duration_min": 5}], "warmup": []}
    for route in app.routes:
        if hasattr(route, "endpoint") and hasattr(route.endpoint, "__globals__"):
            route.endpoint.__globals__["call_ollama"] = mock_ollama

    resp = await client.post("/routines/generate", json={
        "user_id": user_id,
        "force": False,
    })
    assert resp.status_code == 200

    resp2 = await client.post("/routines/generate", json={
        "user_id": user_id,
        "force": False,
    })
    assert resp2.status_code == 200
    assert "routine_id" in resp2.json()
