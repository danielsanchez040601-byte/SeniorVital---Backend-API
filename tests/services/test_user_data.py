"""Tests for UserDataService."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.services.user_data import UserDataService, UserData
from src.database.repositories.user_repository import UserRepository, UserNotFoundError
from src.database.repositories.exercise_repository import ExerciseRepository


@pytest.fixture
def mock_user_repo():
    repo = AsyncMock(spec=UserRepository)
    return repo


@pytest.fixture
def mock_exercise_repo():
    repo = AsyncMock(spec=ExerciseRepository)
    return repo


@pytest.fixture
def service(mock_user_repo, mock_exercise_repo):
    return UserDataService(user_repo=mock_user_repo, exercise_repo=mock_exercise_repo)


@pytest.mark.asyncio
async def test_get_user_data_success(service, mock_user_repo):
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.profile = {"age": 70}
    mock_user.health_profile = {"fitness_level": "bajo"}
    mock_user.preferences = {}

    mock_exercise = MagicMock()
    mock_exercise.id = 10
    mock_exercise.name = "Caminata"
    mock_exercise.description = "Camina suave"
    mock_exercise.level = 1
    mock_exercise.contraindications = ""

    mock_user_repo.get_with_safe_exercises.return_value = (mock_user, [mock_exercise])

    result = await service.get_user_data(user_id=1)

    assert isinstance(result, UserData)
    assert result.user_id == 1
    assert result.profile == {"age": 70}
    assert len(result.safe_exercises) == 1
    assert result.safe_exercises[0]["name"] == "Caminata"


@pytest.mark.asyncio
async def test_get_user_data_not_found(service, mock_user_repo):
    mock_user_repo.get_with_safe_exercises.side_effect = UserNotFoundError(999)

    with pytest.raises(UserNotFoundError):
        await service.get_user_data(user_id=999)


@pytest.mark.asyncio
async def test_get_user_data_empty_profiles(service, mock_user_repo):
    mock_user = MagicMock()
    mock_user.id = 2
    mock_user.profile = None
    mock_user.health_profile = None
    mock_user.preferences = None

    mock_user_repo.get_with_safe_exercises.return_value = (mock_user, [])

    result = await service.get_user_data(user_id=2)

    assert result.profile == {}
    assert result.health_profile == {}
    assert result.safe_exercises == []
