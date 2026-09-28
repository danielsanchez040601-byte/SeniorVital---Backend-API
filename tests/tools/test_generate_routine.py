"""Tests for GenerateRoutineTool — mocked WellnessAgent dependency."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.tools.wellness.generate_routine import GenerateRoutineTool


@pytest.fixture
def mock_agent():
    agent = AsyncMock()
    result = MagicMock()
    result.to_dict.return_value = {
        "id": "42",
        "user_id": "1",
        "exercises": [{"name": "Caminata", "sets": 1, "reps": 10}],
        "generated_by": "ollama",
    }
    result.generated_by = "ollama"
    agent.generate_routine.return_value = result
    return agent


@pytest.fixture
def tool(mock_agent):
    return GenerateRoutineTool(mock_agent)


@pytest.mark.asyncio
async def test_generate_routine_success(tool, mock_agent):
    """Successfully generates a routine."""
    result = await tool.execute(user_id=1)
    assert result.success is True
    assert result.data["generated_by"] == "ollama"
    assert "routine" in result.data
    mock_agent.generate_routine.assert_called_once_with(1, force=False)


@pytest.mark.asyncio
async def test_generate_routine_with_force(tool, mock_agent):
    """Passes force parameter to agent."""
    await tool.execute(user_id=1, force=True)
    mock_agent.generate_routine.assert_called_once_with(1, force=True)


@pytest.mark.asyncio
async def test_generate_routine_agent_failure(tool, mock_agent):
    """Handles agent exception gracefully."""
    mock_agent.generate_routine.side_effect = RuntimeError("LLM timeout")
    result = await tool.execute(user_id=1)
    assert result.success is False
    assert "timeout" in result.error.lower()


@pytest.mark.asyncio
async def test_generate_routine_missing_args(tool):
    """Missing user_id returns error."""
    result = await tool.execute()
    assert result.success is False
    assert "required" in result.error.lower()
