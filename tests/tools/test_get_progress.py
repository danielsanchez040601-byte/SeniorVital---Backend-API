"""Integration tests for GetProgressTool — real PostgreSQL backend."""

import pytest
from src.tools.wellness.get_progress import GetProgressTool


@pytest.fixture
def tool(db_session):
    return GetProgressTool(db_session)


@pytest.mark.asyncio
@pytest.mark.usefixtures("seed_projections", "seed_workout_sessions")
async def test_get_progress_with_data(tool, seed_user):
    """Returns insights and weekly activity when data exists."""
    result = await tool.execute(user_id=seed_user)
    assert result.success is True
    assert len(result.data["insights"]) == 4
    assert result.data["total_sessions"] == 6
    assert len(result.data["weekly_activity"]) > 0


@pytest.mark.asyncio
async def test_get_progress_no_data(tool):
    """Returns empty data for user with no projections."""
    result = await tool.execute(user_id=99999)
    assert result.success is True
    assert result.data["insights"] == []
    assert result.data["total_sessions"] == 0


@pytest.mark.asyncio
@pytest.mark.usefixtures("seed_projections")
async def test_get_progress_custom_weeks(tool, seed_user):
    """Respects custom weeks parameter."""
    result = await tool.execute(user_id=seed_user, weeks=1)
    assert result.success is True
    # Only 1 week of data
    assert len(result.data["insights"]) <= 2


@pytest.mark.asyncio
async def test_get_progress_missing_args(tool):
    """Missing user_id returns error."""
    result = await tool.execute()
    assert result.success is False
    assert "required" in result.error.lower()
