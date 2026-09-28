"""Integration tests for GetRoutineTool — real PostgreSQL backend."""

import pytest
from src.tools.wellness.get_routine import GetRoutineTool


@pytest.fixture
def tool(db_session):
    return GetRoutineTool(db_session)


@pytest.mark.asyncio
@pytest.mark.usefixtures("seed_routine")
async def test_get_routine_exists(tool, seed_user):
    """Returns today's active routine when it exists."""
    result = await tool.execute(user_id=seed_user)
    assert result.success is True
    routine = result.data["routine"]
    assert routine["user_id"] == str(seed_user)
    assert routine["generated_by"] == "test"
    assert len(routine["exercises"]) > 0


@pytest.mark.asyncio
async def test_get_routine_not_exists(tool):
    """Returns error when no routine exists for today."""
    result = await tool.execute(user_id=99999)
    assert result.success is False
    assert "no routine" in result.error.lower()


@pytest.mark.asyncio
async def test_get_routine_missing_args(tool):
    """Missing user_id returns error."""
    result = await tool.execute()
    assert result.success is False
    assert "required" in result.error.lower()
