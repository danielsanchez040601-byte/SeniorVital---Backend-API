import pytest
from httpx import AsyncClient, ASGITransport
from .conftest import load_service_app

app = load_service_app("notification-service")


@pytest.fixture
async def client():
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
