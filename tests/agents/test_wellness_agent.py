"""Tests for WellnessAgent — routine generation with mocked dependencies."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date

from src.agents.wellness.agent import WellnessAgent, RoutineResult, _format_exercises, _clean_llm_response, DEFAULT_ROUTINE
from src.agents.wellness.prompts.routine_builder import RoutinePromptBuilder
from src.services.llm import LLMService, LLMTimeoutError, LLMConnectionError
from src.services.user_data import UserData, UserDataService


# ── Fixtures ──

@pytest.fixture
def mock_llm():
    llm = AsyncMock(spec=LLMService)
    llm.model = "phi3:mini"
    return llm


@pytest.fixture
def mock_user_data():
    svc = AsyncMock(spec=UserDataService)
    svc.get_user_data.return_value = UserData(
        user_id=1,
        profile={"age": 70},
        health_profile={"fitness_level": "principiante", "medical_restrictions": []},
        preferences={"favorite_exercises": []},
        safe_exercises=[{"id": 1, "name": "Caminata", "level": 1, "duration_min": 5, "contraindications": ""}],
    )
    return svc


@pytest.fixture
def mock_routine_repo():
    repo = AsyncMock()
    repo.get_active_by_user_and_date.return_value = None
    saved_routine = MagicMock()
    saved_routine.id = 42
    saved_routine.created_at = MagicMock()
    saved_routine.created_at.isoformat.return_value = "2026-08-23T10:00:00"
    repo.create.return_value = saved_routine
    return repo


@pytest.fixture
def agent(mock_llm, mock_user_data, mock_routine_repo):
    return WellnessAgent(
        llm=mock_llm,
        user_data=mock_user_data,
        routine_repo=mock_routine_repo,
        prompt_builder=RoutinePromptBuilder(),
    )


# ── Tests ──

@pytest.mark.asyncio
async def test_generate_routine_success(agent, mock_llm):
    mock_llm.generate.return_value = json.dumps({
        "exercises": [{"exercise_id": 1, "name": "Caminata", "sets": 2, "reps": 10, "duration_min": 5, "rest_duration_sec": 30}],
        "warmup": [{"name": "Estiramiento", "sets": 1, "reps": 5, "duration_min": 2}],
    })

    result = await agent.generate_routine(user_id=1, force=True)

    assert isinstance(result, RoutineResult)
    assert result.llm_available is True
    assert result.generated_by == "ollama"
    assert len(result.exercises) > 0
    assert result.id == "42"


@pytest.mark.asyncio
async def test_generate_routine_fallback_on_timeout(agent, mock_llm):
    mock_llm.generate.side_effect = LLMTimeoutError("phi3:mini", 600)

    result = await agent.generate_routine(user_id=1, force=True)

    assert result.llm_available is False
    assert result.generated_by == "fallback"
    assert "timeout" in (result.llm_error or "").lower()
    assert len(result.exercises) == len(DEFAULT_ROUTINE["exercises"])


@pytest.mark.asyncio
async def test_generate_routine_fallback_on_connection_error(agent, mock_llm):
    mock_llm.generate.side_effect = LLMConnectionError("http://localhost:11434", Exception("refused"))

    result = await agent.generate_routine(user_id=1, force=True)

    assert result.llm_available is False
    assert result.generated_by == "fallback"


@pytest.mark.asyncio
async def test_generate_routine_returns_existing(agent, mock_routine_repo):
    existing = MagicMock()
    existing.id = 99
    existing.exercises = json.dumps([{"name": "Existing"}])
    existing.warmup = "[]"
    existing.generated_by = "ollama"
    existing.created_at = MagicMock()
    existing.created_at.isoformat.return_value = "2026-08-23T08:00:00"
    mock_routine_repo.get_active_by_user_and_date.return_value = existing

    result = await agent.generate_routine(user_id=1, force=False)

    assert result.id == "99"
    assert result.llm_model == "cached"


@pytest.mark.asyncio
async def test_get_today_routine_exists(agent, mock_routine_repo):
    routine = MagicMock()
    routine.id = 55
    routine.exercises = json.dumps([{"name": "Test"}])
    routine.warmup = "[]"
    routine.generated_by = "ollama"
    routine.created_at = MagicMock()
    routine.created_at.isoformat.return_value = "2026-08-23T09:00:00"
    mock_routine_repo.get_active_by_user_and_date.return_value = routine

    result = await agent.get_today_routine(user_id=1)

    assert result.id == "55"
    assert result.llm_available is True


@pytest.mark.asyncio
async def test_get_today_routine_not_found(agent, mock_routine_repo):
    mock_routine_repo.get_active_by_user_and_date.return_value = None

    with pytest.raises(ValueError, match="No routine for today"):
        await agent.get_today_routine(user_id=1)


# ── Unit tests for helpers ──

def test_format_exercises_basic():
    exercises = [{"exercise_id": 1, "name": "Test", "reps": 10}]
    result = _format_exercises(exercises)
    assert len(result) == 1
    assert result[0]["exercise_id"] == 1
    assert result[0]["reps_per_set"] == 10


def test_format_exercises_empty():
    assert _format_exercises([]) == []


def test_format_exercises_string_json():
    exercises = ['{"exercise_id": 2, "name": "FromJSON", "reps": 5}']
    result = _format_exercises(exercises)
    assert result[0]["name"] == "FromJSON"


def test_clean_llm_response_json_fences():
    raw = '```json\n{"key": "value"}\n```'
    assert _clean_llm_response(raw) == '{"key": "value"}'


def test_clean_llm_response_trailing_comma():
    raw = '{"a": 1, "b": 2,}'
    assert _clean_llm_response(raw) == '{"a": 1, "b": 2}'


def test_clean_llm_response_comments():
    raw = '{"a": 1, // comment\n"b": 2}'
    result = _clean_llm_response(raw)
    assert "//" not in result
