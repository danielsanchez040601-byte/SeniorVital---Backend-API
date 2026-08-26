"""Tests de aceptación para el servicio de catálogo de ejercicios.

Cubre operaciones CRUD, filtros y subida de video.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from .conftest import load_service_app

app = load_service_app("catalog-service")


@pytest.fixture
async def client():
    """Fixture que proporciona un cliente HTTP asíncrono contra la app FastAPI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_exercise(client):
    resp = await client.post("/catalog/exercises", json={
        "name": "Sentadillas asistidas",
        "level": 2,
        "contraindications": ["artrosis_rodilla"],
    })
    assert resp.status_code == 201
    assert "id" in resp.json()


@pytest.mark.asyncio
async def test_list_exercises(client):
    resp = await client.get("/catalog/exercises")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_get_exercise(client):
    resp = await client.post("/catalog/exercises", json={
        "name": "Estiramiento",
        "level": 1,
    })
    ex_id = resp.json()["id"]
    resp = await client.get(f"/catalog/exercises/{ex_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Estiramiento"


@pytest.mark.asyncio
async def test_update_exercise(client):
    resp = await client.post("/catalog/exercises", json={
        "name": "Original",
        "level": 1,
    })
    ex_id = resp.json()["id"]
    resp = await client.put(f"/catalog/exercises/{ex_id}", json={"name": "Updated"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_delete_exercise(client):
    resp = await client.post("/catalog/exercises", json={
        "name": "ToDelete",
        "level": 1,
    })
    ex_id = resp.json()["id"]
    resp = await client.delete(f"/catalog/exercises/{ex_id}")
    assert resp.status_code == 200
    resp = await client.get(f"/catalog/exercises/{ex_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_video_upload_and_serve(client):
    resp = await client.post("/catalog/exercises", json={
        "name": "Video exercise",
        "level": 1,
    })
    ex_id = resp.json()["id"]
    resp = await client.post(
        f"/catalog/exercises/{ex_id}/video",
        files={"file": ("test.mp4", b"fake video content", "video/mp4")},
    )
    assert resp.status_code == 200
    video_url = resp.json()["video_url"]
    assert "http://localhost:8002/storage/videos/" in video_url
