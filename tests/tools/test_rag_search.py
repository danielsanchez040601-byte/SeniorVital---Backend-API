"""Tests for RAGSearchTool — mocked pipeline dependency."""

import pytest
from unittest.mock import AsyncMock
from src.tools.wellness.rag_search import RAGSearchTool


@pytest.fixture
def mock_pipeline():
    pipeline = AsyncMock()
    pipeline.process_query.return_value = {
        "answer": "La caminata es recomendada para adultos mayores.",
        "sources": ["doc1.pdf"],
        "agent": "ExerciseAgent",
        "macrodomain": "A",
        "warnings": [],
    }
    return pipeline


@pytest.fixture
def tool_with_pipeline(mock_pipeline):
    return RAGSearchTool(rag_pipeline=mock_pipeline)


@pytest.fixture
def tool_without_pipeline():
    return RAGSearchTool(rag_pipeline=None)


@pytest.mark.asyncio
async def test_rag_search_success(tool_with_pipeline, mock_pipeline):
    """Successfully queries the RAG pipeline."""
    result = await tool_with_pipeline.execute(query="¿Qué ejercicios puedo hacer?")
    assert result.success is True
    assert "answer" in result.data
    assert result.data["macrodomain"] == "A"
    mock_pipeline.process_query.assert_called_once()


@pytest.mark.asyncio
async def test_rag_search_no_pipeline(tool_without_pipeline):
    """Returns error when pipeline is not available."""
    result = await tool_without_pipeline.execute(query="test")
    assert result.success is False
    assert "not available" in result.error.lower()


@pytest.mark.asyncio
async def test_rag_search_pipeline_failure(tool_with_pipeline, mock_pipeline):
    """Handles pipeline exception gracefully."""
    mock_pipeline.process_query.side_effect = Exception("ChromaDB error")
    result = await tool_with_pipeline.execute(query="test")
    assert result.success is False
    assert "chromadb" in result.error.lower() or "error" in result.error.lower()


@pytest.mark.asyncio
async def test_rag_search_missing_query(tool_with_pipeline):
    """Missing query returns error."""
    result = await tool_with_pipeline.execute()
    assert result.success is False
    assert "required" in result.error.lower()
