"""Tests for database repositories."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date

from src.database.repositories.base import BaseRepository
from src.database.repositories.user_repository import UserRepository, UserNotFoundError
from src.database.repositories.routine_repository import RoutineRepository


# ── BaseRepository ──

def test_base_repository_init():
    mock_session = MagicMock()
    mock_model = MagicMock()
    repo = BaseRepository(mock_session, mock_model)
    assert repo._session is mock_session
    assert repo._model is mock_model


# ── UserRepository ──

@pytest.mark.asyncio
async def test_user_repository_get_by_email():
    mock_session = AsyncMock()
    repo = UserRepository(mock_session, MagicMock())
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = MagicMock(email="test@test.com")
    mock_session.execute.return_value = mock_result

    user = await repo.get_by_email("test@test.com")
    assert user.email == "test@test.com"


@pytest.mark.asyncio
async def test_user_repository_get_with_safe_exercises_not_found():
    mock_session = AsyncMock()
    repo = UserRepository(mock_session, MagicMock())
    mock_session.get.return_value = None

    with pytest.raises(UserNotFoundError):
        await repo.get_with_safe_exercises(999)


# ── RoutineRepository ──

@pytest.mark.asyncio
async def test_routine_repository_get_active_by_user_and_date():
    mock_session = AsyncMock()
    repo = RoutineRepository(mock_session, MagicMock())
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = MagicMock(id=1, active=True)
    mock_session.execute.return_value = mock_result

    routine = await repo.get_active_by_user_and_date(1, date.today())
    assert routine is not None
    assert routine.active is True
