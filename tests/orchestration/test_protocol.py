"""Interaction Protocol tests — correlation, logging, delegation, workflow."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.orchestration import AgentMessage, OrchestrationError
from src.orchestration.agent_protocol import AgentRequest, AgentResponse, IntentResult
from src.orchestration.logging import OrchestrationLogger, create_timer
from src.orchestration.protocol import (
    DelegateCallback,
    StepResult,
    WorkflowEngine,
    WorkflowStep,
)
from src.orchestration.router import OrchestratorAgent


# ── Fixtures ──


@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.generate = AsyncMock()
    llm.model = "phi3:mini"
    return llm


@pytest.fixture
def orchestrator(mock_llm):
    return OrchestratorAgent(mock_llm)


@pytest.fixture
def mock_agent():
    agent = AsyncMock()
    agent.name = "test_agent"
    agent.domain = "test"
    agent.description = "Test agent"
    agent.handle = AsyncMock(
        return_value=AgentResponse(
            text="Test response",
            safety_level="safe",
            tool_chain=["test_tool"],
            metadata={"key": "value"},
        )
    )
    return agent


@pytest.fixture
def critical_agent():
    agent = AsyncMock()
    agent.name = "dangerous_agent"
    agent.domain = "danger"
    agent.handle = AsyncMock(
        return_value=AgentResponse(
            text="Do something risky!",
            safety_level="critical",
            tool_chain=[],
        )
    )
    return agent


@pytest.fixture
def fallback_agent():
    agent = AsyncMock()
    agent.name = "fallback"
    agent.domain = "general"
    agent.handle = AsyncMock(
        return_value=AgentResponse(
            text="Fallback response",
            safety_level="safe",
            tool_chain=[],
        )
    )
    return agent


# ── AgentMessage Tests ──


class TestAgentMessage:
    """Tests for enhanced AgentMessage."""

    def test_correlation_id_auto_generated(self):
        msg = AgentMessage(
            from_agent="user",
            to_agent="orchestrator",
            content={"message": "test"},
            message_type="query",
        )
        assert msg.correlation_id != ""
        assert len(msg.correlation_id) == 12

    def test_correlation_id_unique(self):
        msg1 = AgentMessage(from_agent="a", to_agent="b", content={}, message_type="query")
        msg2 = AgentMessage(from_agent="a", to_agent="b", content={}, message_type="query")
        assert msg1.correlation_id != msg2.correlation_id

    def test_timestamp_auto_generated(self):
        msg = AgentMessage(from_agent="a", to_agent="b", content={}, message_type="query")
        assert msg.timestamp != ""
        assert "T" in msg.timestamp  # ISO-8601 format

    def test_parent_id_default_empty(self):
        msg = AgentMessage(from_agent="a", to_agent="b", content={}, message_type="query")
        assert msg.parent_id == ""

    def test_correlation_id_propagated(self):
        original_id = "abc123def456"
        msg = AgentMessage(
            from_agent="user",
            to_agent="orchestrator",
            content={"message": "test"},
            message_type="query",
            correlation_id=original_id,
        )
        response = AgentMessage(
            from_agent="orchestrator",
            to_agent="user",
            content={"response": "ok"},
            message_type="response",
            correlation_id=msg.correlation_id,
        )
        assert response.correlation_id == original_id


# ── OrchestrationLogger Tests ──


class TestOrchestrationLogger:
    """Tests for structured logging."""

    def test_route_start_emits_event(self):
        log = OrchestrationLogger()
        with patch.object(log, "_emit") as mock_emit:
            log.route_start("corr123", 1, "¿Qué como?")
            mock_emit.assert_called_once()
            args = mock_emit.call_args
            assert args[0][0] == "route_start"
            assert args[0][1] == "corr123"
            assert args[0][2]["user_id"] == 1

    def test_delegation_end_includes_timing(self):
        log = OrchestrationLogger()
        with patch.object(log, "_emit") as mock_emit:
            log.delegation_end("corr123", "agent_a", "agent_b", 150.5, True, "safe")
            data = mock_emit.call_args[0][2]
            assert data["duration_ms"] == 150.5
            assert data["success"] is True
            assert data["safety_level"] == "safe"

    def test_safety_check_blocked(self):
        log = OrchestrationLogger()
        with patch.object(log, "_emit") as mock_emit:
            log.safety_check("corr123", "agent_a", "critical", True)
            data = mock_emit.call_args[0][2]
            assert data["blocked"] is True
            assert data["level"] == "critical"


# ── create_timer Tests ──


class TestCreateTimer:
    """Tests for timer utility."""

    def test_timer_returns_callable(self):
        timer = create_timer()
        assert callable(timer[0])

    def test_timer_measures_elapsed(self):
        import time
        timer = create_timer()
        # Use a busy-wait to guarantee measurable time passes on Windows
        end = time.monotonic() + 0.02
        while time.monotonic() < end:
            pass
        elapsed = timer[0]()
        assert elapsed > 0


# ── Delegate Safety Tests ──


class TestDelegateSafety:
    """Tests for safety validation in delegate()."""

    @pytest.mark.asyncio
    async def test_delegate_returns_full_response(self, orchestrator, mock_agent):
        orchestrator.register_agent("test", mock_agent)
        result = await orchestrator.delegate("workflow", "test", {"message": "hi", "user_id": 1})
        assert "text" in result
        assert "safety_level" in result
        assert "tool_chain" in result
        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_delegate_blocks_critical_response(self, orchestrator, critical_agent):
        orchestrator.register_agent("danger", critical_agent)
        result = await orchestrator.delegate("workflow", "danger", {"message": "test"})
        assert result["safety_level"] == "critical"
        assert result["blocked"] is True
        assert "profesional" in result["text"]

    @pytest.mark.asyncio
    async def test_delegate_propagates_correlation_id(self, orchestrator, mock_agent):
        orchestrator.register_agent("test", mock_agent)
        result = await orchestrator.delegate(
            "workflow", "test", {"message": "hi"}, correlation_id="test_corr_123"
        )
        # Verify the agent received the correlation_id in context
        call_args = mock_agent.handle.call_args[0][0]
        assert call_args.context["correlation_id"] == "test_corr_123"

    @pytest.mark.asyncio
    async def test_delegate_agent_error_propagates(self, orchestrator):
        failing_agent = AsyncMock()
        failing_agent.name = "failing"
        failing_agent.handle = AsyncMock(side_effect=Exception("boom"))
        orchestrator.register_agent("fail", failing_agent)

        with pytest.raises(Exception, match="boom"):
            await orchestrator.delegate("workflow", "fail", {"message": "test"})


# ── WorkflowEngine Tests ──


class TestWorkflowEngine:
    """Tests for multi-agent workflow execution."""

    @pytest.mark.asyncio
    async def test_execute_single_step(self, orchestrator, mock_agent):
        orchestrator.register_agent("analytics", mock_agent)
        engine = WorkflowEngine(orchestrator)

        steps = [WorkflowStep(agent="analytics", task_template={"message": "progress", "user_id": 1})]
        results = await engine.execute(steps, {"user_id": 1}, correlation_id="wf_001")

        assert len(results) == 1
        assert results[0].success is True
        assert results[0].agent == "analytics"
        assert results[0].response.text == "Test response"

    @pytest.mark.asyncio
    async def test_execute_multi_step(self, orchestrator):
        agent_a = AsyncMock()
        agent_a.name = "agent_a"
        agent_a.handle = AsyncMock(
            return_value=AgentResponse(text="Step A result", safety_level="safe", tool_chain=[])
        )
        agent_b = AsyncMock()
        agent_b.name = "agent_b"
        agent_b.handle = AsyncMock(
            return_value=AgentResponse(text="Step B result", safety_level="safe", tool_chain=[])
        )

        orchestrator.register_agent("agent_a", agent_a)
        orchestrator.register_agent("agent_b", agent_b)

        engine = WorkflowEngine(orchestrator)
        steps = [
            WorkflowStep(agent="agent_a", task_template={"message": "step1", "user_id": 1}),
            WorkflowStep(agent="agent_b", task_template={"message": "{prev.text}", "user_id": 1}),
        ]
        results = await engine.execute(steps, {"user_id": 1})

        assert len(results) == 2
        assert results[0].response.text == "Step A result"
        assert results[1].response.text == "Step B result"
        # Verify agent_b received agent_a's result
        agent_b_call = agent_b.handle.call_args[0][0]
        assert "Step A result" in agent_b_call.message

    @pytest.mark.asyncio
    async def test_execute_step_failure(self, orchestrator):
        failing_agent = AsyncMock()
        failing_agent.name = "failing"
        failing_agent.handle = AsyncMock(side_effect=Exception("crash"))

        ok_agent = AsyncMock()
        ok_agent.name = "ok"
        ok_agent.handle = AsyncMock(
            return_value=AgentResponse(text="OK", safety_level="safe", tool_chain=[])
        )

        orchestrator.register_agent("failing", failing_agent)
        orchestrator.register_agent("ok", ok_agent)

        engine = WorkflowEngine(orchestrator)
        steps = [
            WorkflowStep(agent="failing", task_template={"message": "fail", "user_id": 1}),
            WorkflowStep(agent="ok", task_template={"message": "recover", "user_id": 1}),
        ]
        results = await engine.execute(steps, {"user_id": 1})

        assert results[0].success is False
        assert results[0].error == "crash"
        assert results[1].success is True

    @pytest.mark.asyncio
    async def test_condition_skip_step(self, orchestrator):
        agent_a = AsyncMock()
        agent_a.name = "agent_a"
        agent_a.handle = AsyncMock(
            return_value=AgentResponse(text="result", safety_level="critical", tool_chain=[])
        )
        agent_b = AsyncMock()
        agent_b.name = "agent_b"

        orchestrator.register_agent("agent_a", agent_a)
        orchestrator.register_agent("agent_b", agent_b)

        engine = WorkflowEngine(orchestrator)
        steps = [
            WorkflowStep(agent="agent_a", task_template={"message": "check", "user_id": 1}),
            WorkflowStep(
                agent="agent_b",
                task_template={"message": "proceed", "user_id": 1},
                condition="prev.safety_level != 'critical'",
            ),
        ]
        results = await engine.execute(steps, {"user_id": 1})

        assert results[0].success is True
        assert results[1].skipped is True
        agent_b.handle.assert_not_called()


# ── Full Flow Correlation Test ──


class TestFullFlowCorrelation:
    """Tests for end-to-end correlation tracing."""

    @pytest.mark.asyncio
    async def test_route_generates_and_returns_correlation_id(self, orchestrator, mock_agent, mock_llm):
        orchestrator.register_agent("test", mock_agent)
        mock_llm.generate = AsyncMock(
            return_value=json.dumps({"domain": "test", "confidence": 0.9})
        )

        msg = AgentMessage(
            from_agent="user",
            to_agent="orchestrator",
            content={"message": "test", "user_id": 1},
            message_type="query",
        )
        response = await orchestrator.route(msg)

        assert response.correlation_id != ""
        assert response.correlation_id == msg.correlation_id

    @pytest.mark.asyncio
    async def test_route_logs_structured_events(self, orchestrator, mock_agent, mock_llm):
        orchestrator.register_agent("test", mock_agent)
        mock_llm.generate = AsyncMock(
            return_value=json.dumps({"domain": "test", "confidence": 0.9})
        )

        msg = AgentMessage(
            from_agent="user",
            to_agent="orchestrator",
            content={"message": "test", "user_id": 1},
            message_type="query",
        )

        with patch("src.orchestration.router._orchestration_log") as mock_log:
            await orchestrator.route(msg)
            # Verify structured logging was called
            mock_log.route_start.assert_called_once()
            mock_log.intent_classified.assert_called_once()
            mock_log.agent_selected.assert_called_once()
            mock_log.route_end.assert_called_once()
