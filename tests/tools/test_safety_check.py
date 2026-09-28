"""Integration tests for SafetyCheckTool — real PostgreSQL backend."""

import pytest
from src.tools.wellness.safety_check import SafetyCheckTool


@pytest.fixture
def tool(db_session):
    return SafetyCheckTool(db_session)


@pytest.mark.asyncio
@pytest.mark.usefixtures("seed_user_with_restrictions", "seed_exercises")
async def test_unsafe_activity_detected(tool, seed_user_with_restrictions):
    """Activity containing a restricted keyword is flagged as unsafe."""
    result = await tool.execute(user_id=seed_user_with_restrictions, activity="yoga para artritis")
    assert result.success is True
    assert result.data["safe"] is False
    assert len(result.data["warnings"]) > 0
    assert any("artritis" in w.lower() for w in result.data["warnings"])


@pytest.mark.asyncio
@pytest.mark.usefixtures("seed_user", "seed_exercises")
async def test_safe_activity(tool, seed_user):
    """Activity without conflicting restrictions is safe."""
    result = await tool.execute(user_id=seed_user, activity="caminata ligera")
    assert result.success is True
    assert result.data["safe"] is True
    assert len(result.data["restrictions"]) == 0


@pytest.mark.asyncio
async def test_unknown_user(tool):
    """Non-existent user returns error."""
    result = await tool.execute(user_id=99999, activity="caminata")
    assert result.success is False
    assert "not found" in result.error.lower()


@pytest.mark.asyncio
@pytest.mark.usefixtures("seed_user")
async def test_no_restrictions_user(tool, seed_user):
    """User without medical restrictions has empty restrictions list."""
    result = await tool.execute(user_id=seed_user, activity="cualquier cosa")
    assert result.success is True
    assert result.data["restrictions"] == []


@pytest.mark.asyncio
async def test_missing_args(tool):
    """Missing required args returns error."""
    result = await tool.execute(user_id=1)
    assert result.success is False
    assert "required" in result.error.lower()
