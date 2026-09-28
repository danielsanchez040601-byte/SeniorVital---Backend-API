"""Integration tests for ExerciseCatalogTool — real PostgreSQL backend."""

import pytest
from src.tools.wellness.exercise_catalog import ExerciseCatalogTool


@pytest.fixture
def tool(db_session):
    return ExerciseCatalogTool(db_session)


@pytest.mark.asyncio
@pytest.mark.usefixtures("seed_exercises")
async def test_search_all_exercises(tool):
    """Returns all exercises when no filters applied."""
    result = await tool.execute()
    assert result.success is True
    assert result.data["count"] == 5
    assert len(result.data["exercises"]) == 5


@pytest.mark.asyncio
@pytest.mark.usefixtures("seed_exercises")
async def test_search_by_level(tool):
    """Filters exercises by functional level."""
    result = await tool.execute(level=1)
    assert result.success is True
    assert result.data["count"] == 2  # Caminata ligera + Natación
    names = {ex["name"] for ex in result.data["exercises"]}
    assert "Caminata ligera" in names
    assert "Natación" in names


@pytest.mark.asyncio
@pytest.mark.usefixtures("seed_exercises")
async def test_search_by_keyword(tool):
    """Filters exercises by keyword in name/description."""
    result = await tool.execute(keyword="yoga")
    assert result.success is True
    assert result.data["count"] == 1
    assert result.data["exercises"][0]["name"] == "Yoga suave"


@pytest.mark.asyncio
@pytest.mark.usefixtures("seed_exercises")
async def test_exclude_contraindications(tool):
    """Excludes exercises matching contraindications."""
    result = await tool.execute(exclude_contraindications=["artritis"])
    assert result.success is True
    # Excludes Yoga (artritis) and Trote (artritis,hipertension)
    names = {ex["name"] for ex in result.data["exercises"]}
    assert "Yoga suave" not in names
    assert "Trote" not in names
    assert "Caminata ligera" in names
    assert "Natación" in names


@pytest.mark.asyncio
async def test_invalid_level_returns_error(tool):
    """level outside 1-4 range returns error."""
    result = await tool.execute(level=5)
    assert result.success is False
    assert "Invalid" in result.error
