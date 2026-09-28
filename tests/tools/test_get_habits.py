"""Integration tests for GetHabitsTool — real PostgreSQL backend."""

import pytest
from src.tools.wellness.get_habits import GetHabitsTool


@pytest.fixture
def tool(db_session):
    return GetHabitsTool(db_session)


@pytest.mark.asyncio
@pytest.mark.usefixtures("seed_habits")
async def test_get_habits_default_days(tool, seed_user):
    """Returns habits for last 7 days by default."""
    result = await tool.execute(user_id=seed_user)
    assert result.success is True
    assert result.data["count"] == 7
    assert len(result.data["habits"]) == 7
    # All should have water > 0
    for h in result.data["habits"]:
        assert h["water_glasses"] > 0


@pytest.mark.asyncio
@pytest.mark.usefixtures("seed_habits")
async def test_get_habits_custom_days(tool, seed_user):
    """Respects custom days parameter (returns fewer records than default 7)."""
    result_default = await tool.execute(user_id=seed_user, days=7)
    result_short = await tool.execute(user_id=seed_user, days=3)
    assert result_short.success is True
    assert result_short.data["count"] < result_default.data["count"]


@pytest.mark.asyncio
async def test_get_habits_no_data(tool):
    """Returns empty list when user has no habits."""
    result = await tool.execute(user_id=99999)
    assert result.success is True
    assert result.data["count"] == 0
    assert result.data["habits"] == []


@pytest.mark.asyncio
async def test_get_habits_missing_args(tool):
    """Missing user_id returns error."""
    result = await tool.execute()
    assert result.success is False
    assert "required" in result.error.lower()
