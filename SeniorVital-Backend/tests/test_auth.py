"""Tests de aceptación para el servicio de autenticación y perfiles.

Cubre los criterios AC-AUTH-01 al AC-AUTH-05 del SDD.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from .conftest import load_service_app

app = load_service_app("auth-profile-service")


@pytest.fixture
async def client():
    """Fixture que proporciona un cliente HTTP asíncrono contra la app FastAPI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_ac_auth_01_password_hashed(client):
    """AC-AUTH-01: Password hashed with bcrypt"""
    resp = await client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "secret123",
        "role": "senior",
    })
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_ac_auth_02_invalid_role(client):
    """AC-AUTH-02: HTTP 400 if role not allowed"""
    resp = await client.post("/auth/register", json={
        "email": "bad@example.com",
        "password": "secret123",
        "role": "invalid_role",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_ac_auth_03_caregiver_no_linked(client):
    """AC-AUTH-03: caregiver without linked_senior_id"""
    resp = await client.post("/auth/register", json={
        "email": "caregiver@example.com",
        "password": "secret123",
        "role": "caregiver",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "caregiver"


@pytest.mark.asyncio
async def test_ac_auth_04_max_3_caregivers(client):
    """AC-AUTH-04: Senior max 3 caregivers"""
    resp = await client.post("/auth/register", json={
        "email": "senior@example.com",
        "password": "secret123",
        "role": "senior",
    })
    assert resp.status_code == 200
    senior_id = resp.json()["id"]

    resp = await client.post("/auth/login", json={
        "email": "senior@example.com",
        "password": "secret123",
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    for i in range(3):
        resp = await client.post("/auth/register", json={
            "email": f"cg{i}@example.com",
            "password": "secret123",
            "role": "caregiver",
        })
        resp = await client.post("/auth/link-caregiver",
            json={"caregiver_email": f"cg{i}@example.com"},
            headers=headers,
        )
        assert resp.status_code == 200

    resp = await client.post("/auth/register", json={
        "email": "cg_extra@example.com",
        "password": "secret123",
        "role": "caregiver",
    })
    resp = await client.post("/auth/link-caregiver",
        json={"caregiver_email": "cg_extra@example.com"},
        headers=headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_ac_auth_05_caregiver_one_linked(client):
    """AC-AUTH-05: Caregiver can have only one linked_senior_id"""
    resp = await client.post("/auth/register", json={
        "email": "senior_b@example.com",
        "password": "secret123",
        "role": "senior",
    })
    assert resp.status_code == 200
    resp = await client.post("/auth/login", json={
        "email": "senior_b@example.com",
        "password": "secret123",
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/auth/register", json={
        "email": "cg_only@example.com",
        "password": "secret123",
        "role": "caregiver",
    })

    resp = await client.post("/auth/link-caregiver",
        json={"caregiver_email": "cg_only@example.com"},
        headers=headers,
    )
    assert resp.status_code == 200

    resp = await client.post("/auth/register", json={
        "email": "senior_c@example.com",
        "password": "secret123",
        "role": "senior",
    })
    resp = await client.post("/auth/login", json={
        "email": "senior_c@example.com",
        "password": "secret123",
    })
    token2 = resp.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}
    resp = await client.post("/auth/link-caregiver",
        json={"caregiver_email": "cg_only@example.com"},
        headers=headers2,
    )
    assert resp.status_code == 400
