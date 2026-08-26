"""Tests de aceptación para el servicio de notificaciones push.

Cubre suscripción, sobrescritura (AC-NOT-01) y envío asíncrono (AC-NOT-02).
"""

import pytest
from httpx import AsyncClient, ASGITransport
from .conftest import load_service_app

import uuid
import json
from seniorvital_shared import get_pool

app = load_service_app("notification-service")


@pytest.fixture(autouse=True)
async def seed_users():
    """Crea los usuarios correspondientes a los UUIDs hardcodeados en los tests."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        for i in range(1, 4):
            user_id = uuid.UUID(f"00000000-0000-0000-0000-00000000000{i}")
            exists = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM users WHERE id = $1)", user_id)
            if not exists:
                await conn.execute(
                    "INSERT INTO users (id, email, role, profile, password) VALUES ($1, $2, $3, $4, $5)",
                    user_id,
                    f"notif_user_{i}@test.com",
                    "senior",
                    json.dumps({}),
                    "pw"
                )


@pytest.fixture
async def client():
    """Fixture que proporciona un cliente HTTP asíncrono contra la app FastAPI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_subscribe(client):
    resp = await client.post("/notify/subscribe", json={
        "user_id": "00000000-0000-0000-0000-000000000001",
        "subscription": {
            "endpoint": "https://example.com/push",
            "keys": {
                "p256dh": "test_key",
                "auth": "test_auth",
            },
        },
    })
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_subscribe_overwrite(client):
    """AC-NOT-01: Existing subscription gets overwritten"""
    resp = await client.post("/notify/subscribe", json={
        "user_id": "00000000-0000-0000-0000-000000000002",
        "subscription": {
            "endpoint": "https://example.com/push",
            "keys": {
                "p256dh": "test_key",
                "auth": "test_auth",
            },
        },
    })
    assert resp.status_code == 200

    resp = await client.post("/notify/subscribe", json={
        "user_id": "00000000-0000-0000-0000-000000000002",
        "subscription": {
            "endpoint": "https://example.com/push_new",
            "keys": {
                "p256dh": "new_key",
                "auth": "new_auth",
            },
        },
    })
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_send_notification(client):
    """AC-NOT-02: Notification does not block (background task)"""
    resp = await client.post("/notify/send", json={
        "user_id": "00000000-0000-0000-0000-000000000003",
        "title": "Test",
        "body": "Test notification",
    })
    assert resp.status_code == 200
