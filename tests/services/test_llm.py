"""Tests for LLMService."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.services.llm import LLMService, LLMTimeoutError, LLMConnectionError


@pytest.fixture
def llm_service():
    return LLMService(base_url="http://localhost:11434", model="phi3:mini", timeout=10.0)


def test_llm_service_init():
    svc = LLMService(base_url="http://test:11434", model="test-model", timeout=30.0)
    assert svc.model == "test-model"


def test_llm_service_default_model():
    svc = LLMService()
    assert svc.model == "phi3:mini"


@pytest.mark.asyncio
async def test_llm_service_generate_success(llm_service):
    with patch.object(llm_service._client, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = '{"exercises": []}'
        result = await llm_service.generate("test prompt", format_json=True)
        assert result == '{"exercises": []}'
        mock_gen.assert_called_once_with("test prompt", system=None, format_json=True)


@pytest.mark.asyncio
async def test_llm_service_generate_connection_error(llm_service):
    with patch.object(llm_service._client, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = ConnectionError("refused")
        with pytest.raises(LLMConnectionError):
            await llm_service.generate("test prompt")


@pytest.mark.asyncio
async def test_llm_service_health_check(llm_service):
    with patch.object(llm_service._client, "health_check", new_callable=AsyncMock) as mock_hc:
        mock_hc.return_value = True
        result = await llm_service.health_check()
        assert result is True
