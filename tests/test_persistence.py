import pytest
import json
from seniorvital_shared import HealthProfile


def test_health_profile_valid():
    profile = HealthProfile(
        age=70,
        weight_kg=70.0,
        height_cm=165.0,
        fitness_level="principiante",
        goals=["mejorar_movilidad"],
    )
    assert profile.age == 70


def test_health_profile_invalid_restriction():
    with pytest.raises(ValueError):
        HealthProfile(
            age=70,
            weight_kg=70.0,
            height_cm=165.0,
            fitness_level="principiante",
            goals=["mejorar_movilidad"],
            medical_restrictions=["invalid_restriction"],
        )


@pytest.mark.asyncio
async def test_pers_03_caregiver_linked_senior(auto_init_pool):
    """AC-PERS-03: linked_senior_id only non-null when role=caregiver"""
    from seniorvital_shared import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        senior = await conn.fetchrow(
            "INSERT INTO users (email, role, profile, password) VALUES ($1, $2, $3, $4) RETURNING id",
            "senior_pers@test.com",
            "senior",
            json.dumps({}),
            "pw",
        )
        await conn.execute(
            "INSERT INTO users (email, role, profile, linked_senior_id, password) VALUES ($1, $2, $3, $4, $5)",
            "caregiver_pers@test.com",
            "caregiver",
            json.dumps({}),
            senior["id"],
            "pw",
        )
        caregiver = await conn.fetchrow("SELECT * FROM users WHERE email = $1", "caregiver_pers@test.com")
        assert caregiver["linked_senior_id"] == senior["id"]


@pytest.mark.asyncio
async def test_event_queue_insert(auto_init_pool):
    """Test that event_queue inserts work"""
    from seniorvital_shared import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO event_queue (stream_name, payload) VALUES ($1, $2)",
            "test-event",
            json.dumps({"test": True}),
        )
        row = await conn.fetchrow("SELECT * FROM event_queue WHERE stream_name = $1", "test-event")
        assert row is not None
        payload = json.loads(row["payload"])
        assert payload["test"] is True
        assert row["processed"] is False
