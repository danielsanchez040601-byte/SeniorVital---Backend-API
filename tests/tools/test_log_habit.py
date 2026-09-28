"""Integration tests for LogHabitTool — real PostgreSQL backend."""

import pytest
from datetime import date
from src.tools.wellness.log_habit import LogHabitTool


@pytest.fixture
def tool(db_session):
    return LogHabitTool(db_session)


@pytest.mark.asyncio
@pytest.mark.usefixtures("seed_user")
async def test_log_water(tool, seed_user):
    """Logs water intake for today."""
    result = await tool.execute(user_id=seed_user, habit_type="water", value=8)
    assert result.success is True
    assert result.data["logged"] is True
    assert result.data["type"] == "water"
    assert result.data["value"] == 8
    assert result.data["date"] == date.today().isoformat()


@pytest.mark.asyncio
@pytest.mark.usefixtures("seed_user")
async def test_log_sleep(tool, seed_user):
    """Logs sleep hours for today."""
    result = await tool.execute(user_id=seed_user, habit_type="sleep", value=7.5)
    assert result.success is True
    assert result.data["type"] == "sleep"
    assert result.data["value"] == 7.5


@pytest.mark.asyncio
@pytest.mark.usefixtures("seed_user")
async def test_upsert_overwrites(tool, seed_user):
    """Logging same habit twice updates the value (UPSERT)."""
    await tool.execute(user_id=seed_user, habit_type="water", value=6)
    result = await tool.execute(user_id=seed_user, habit_type="water", value=10)
    assert result.success is True
    assert result.data["value"] == 10


@pytest.mark.asyncio
async def test_invalid_habit_type(tool):
    """Invalid habit_type returns error."""
    result = await tool.execute(user_id=1, habit_type="exercise", value=30)
    assert result.success is False
    assert "required" in result.error.lower()


@pytest.mark.asyncio
async def test_missing_args(tool):
    """Missing required args returns error."""
    result = await tool.execute(user_id=1)
    assert result.success is False
    assert "required" in result.error.lower()
