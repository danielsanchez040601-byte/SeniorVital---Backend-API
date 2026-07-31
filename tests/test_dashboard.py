import pytest
from httpx import AsyncClient, ASGITransport
from .conftest import load_service_app

app = load_service_app("dashboard-service")


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_progress_user_not_found(client):
    resp = await client.get("/dashboard/progress/00000000-0000-0000-0000-000000000099")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_projection_null(client):
    resp = await client.get("/dashboard/projection/00000000-0000-0000-0000-000000000099")
    assert resp.status_code == 200
    assert resp.json()["projection"] is None


@pytest.mark.asyncio
async def test_insights_empty(client):
    resp = await client.get("/dashboard/insights/00000000-0000-0000-0000-000000000099")
    assert resp.status_code == 200
    assert resp.json() == []
