"""Multi-Agent Integration Tests — routing, delegation, collaboration, performance, traceability.

End-to-end tests that wire multiple agents through the OrchestratorAgent
and validate the complete flow from user message to response.

Usage:
    pytest tests/integration/ -v
    pytest tests/integration/ -v -k "performance"
    pytest tests/integration/ -v -k "traceability"
"""

from __future__ import annotations

import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.orchestration import AgentMessage
from src.orchestration.agent_protocol import AgentResponse
from src.orchestration.logging import OrchestrationLogger
from src.orchestration.protocol import StepResult, WorkflowEngine, WorkflowStep
from src.orchestration.router import OrchestratorAgent

# Helpers are in conftest.py (same directory)


def make_user_message(text: str, user_id: int = 1, correlation_id: str = "") -> AgentMessage:
    """Create a user AgentMessage."""
    kwargs = {
        "from_agent": "user",
        "to_agent": "orchestrator",
        "content": {"message": text, "user_id": user_id},
        "message_type": "query",
    }
    if correlation_id:
        kwargs["correlation_id"] = correlation_id
    return AgentMessage(**kwargs)


def make_classification_response(domain: str, confidence: float = 0.9) -> str:
    """Create a mock LLM classification response."""
    return json.dumps({"domain": domain, "confidence": confidence, "reason": "test"})


# ════════════════════════════════════════════════════════════════
# GROUP 1: Domain Routing (4 tests)
# ════════════════════════════════════════════════════════════════


class TestDomainRouting:
    """Validate that IntentClassifier routes to the correct agent by domain."""

    @pytest.mark.asyncio
    async def test_nutrition_keyword_routing(self, wired_orchestrator, mock_llm, nutrition_agent):
        """'¿Qué debo comer hoy?' → nutrition via keywords."""
        # Override classifier to use keyword path
        wired_orchestrator._classifier = MagicMock()
        wired_orchestrator._classifier.classify = AsyncMock(
            return_value=MagicMock(domain="nutrition", confidence=0.85, keywords=["comer"])
        )

        msg = make_user_message("¿Qué debo comer hoy?")
        response = await wired_orchestrator.route(msg)

        assert response.content["agent"] == "nutrition"
        nutrition_agent.handle.assert_called_once()
        assert response.content["safety_level"] == "safe"

    @pytest.mark.asyncio
    async def test_analytics_keyword_routing(self, wired_orchestrator, mock_llm, analytics_agent):
        """'¿Cómo voy con mis ejercicios?' → analytics via keywords."""
        wired_orchestrator._classifier = MagicMock()
        wired_orchestrator._classifier.classify = AsyncMock(
            return_value=MagicMock(domain="analytics", confidence=0.9, keywords=["ejercicio"])
        )

        msg = make_user_message("¿Cómo voy con mis ejercicios?")
        response = await wired_orchestrator.route(msg)

        assert response.content["agent"] == "analytics"
        analytics_agent.handle.assert_called_once()

    @pytest.mark.asyncio
    async def test_motivation_keyword_routing(self, wired_orchestrator, mock_llm, motivation_agent):
        """'Me siento triste y aburrido' → motivation via keywords."""
        wired_orchestrator._classifier = MagicMock()
        wired_orchestrator._classifier.classify = AsyncMock(
            return_value=MagicMock(domain="motivation", confidence=0.8, keywords=["triste"])
        )

        msg = make_user_message("Me siento triste y aburrido")
        response = await wired_orchestrator.route(msg)

        assert response.content["agent"] == "motivation"
        motivation_agent.handle.assert_called_once()

    @pytest.mark.asyncio
    async def test_safety_keyword_routing(self, wired_orchestrator, mock_llm):
        """'¿Es seguro correr con presión alta?' → safety via keywords."""
        safety_agent = AsyncMock()
        safety_agent.name = "safety_guardian"
        safety_agent.domain = "safety"
        safety_agent.handle = AsyncMock(
            return_value=AgentResponse(
                text="Con presión alta, consulta a tu médico antes de hacer ejercicio.",
                safety_level="safe",
                tool_chain=["safety_check"],
            )
        )
        wired_orchestrator.register_agent("safety", safety_agent)
        wired_orchestrator._classifier = MagicMock()
        wired_orchestrator._classifier.classify = AsyncMock(
            return_value=MagicMock(domain="safety", confidence=0.95, keywords=["presión alta"])
        )

        msg = make_user_message("¿Es seguro correr con presión alta?")
        response = await wired_orchestrator.route(msg)

        assert response.content["agent"] == "safety_guardian"
        safety_agent.handle.assert_called_once()


# ════════════════════════════════════════════════════════════════
# GROUP 2: Delegation & Safety (3 tests)
# ════════════════════════════════════════════════════════════════


class TestDelegationSafety:
    """Validate safety blocking and delegation behavior."""

    @pytest.mark.asyncio
    async def test_critical_response_blocked(self, wired_orchestrator, mock_llm, critical_agent):
        """Agent returns safety_level='critical' → orchestrator blocks response."""
        wired_orchestrator.register_agent("danger", critical_agent)
        wired_orchestrator._classifier = MagicMock()
        wired_orchestrator._classifier.classify = AsyncMock(
            return_value=MagicMock(domain="danger", confidence=0.9)
        )

        msg = make_user_message("test dangerous query")
        response = await wired_orchestrator.route(msg)

        assert response.content["safety_level"] == "critical"
        assert "profesional" in response.content["response"].lower()

    @pytest.mark.asyncio
    async def test_agent_exception_fallback(self, wired_orchestrator, mock_llm, failing_agent):
        """Agent raises exception → fallback agent handles."""
        wired_orchestrator.register_agent("fail", failing_agent)
        wired_orchestrator._classifier = MagicMock()
        wired_orchestrator._classifier.classify = AsyncMock(
            return_value=MagicMock(domain="fail", confidence=0.9)
        )

        msg = make_user_message("test failing query")
        response = await wired_orchestrator.route(msg)

        # Should fall back to wellness_coach — check response text, not agent name
        # (agent_name in content is the original agent, not the fallback)
        assert "bienestar" in response.content["response"].lower() or "ayudar" in response.content["response"].lower()

    @pytest.mark.asyncio
    async def test_delegate_critical_blocks(self, wired_orchestrator):
        """delegate() blocks critical response from target agent."""
        danger_agent = AsyncMock()
        danger_agent.name = "danger"
        danger_agent.handle = AsyncMock(
            return_value=AgentResponse(text="Danger!", safety_level="critical", tool_chain=[])
        )
        wired_orchestrator.register_agent("danger", danger_agent)

        result = await wired_orchestrator.delegate(
            "workflow", "danger", {"message": "test", "user_id": 1}
        )

        assert result["safety_level"] == "critical"
        assert result["blocked"] is True


# ════════════════════════════════════════════════════════════════
# GROUP 3: Multi-Agent Collaboration (3 tests)
# ════════════════════════════════════════════════════════════════


class TestMultiAgentCollaboration:
    """Validate workflow engine and agent-to-agent collaboration."""

    @pytest.mark.asyncio
    async def test_workflow_chaining(self, wired_orchestrator):
        """Workflow: nutrition → analytics chains results via {prev.text}."""
        engine = WorkflowEngine(wired_orchestrator)
        steps = [
            WorkflowStep(
                agent="nutrition",
                task_template={"message": "dieta para diabetes", "user_id": 1},
            ),
            WorkflowStep(
                agent="analytics",
                task_template={"message": "progreso del usuario: {prev.text}", "user_id": 1},
            ),
        ]

        results = await engine.execute(steps, {"user_id": 1}, correlation_id="wf_test_01")

        assert len(results) == 2
        assert results[0].success is True
        assert results[0].agent == "nutrition"
        assert results[1].success is True
        assert results[1].agent == "analytics"
        # Verify chaining: analytics received nutrition's text
        analytics_call = wired_orchestrator._agents["analytics"].handle.call_args
        assert "buena nutrición" in analytics_call[0][0].message

    @pytest.mark.asyncio
    async def test_workflow_conditional_skip(self, wired_orchestrator):
        """Workflow skips step when condition is not met."""
        # Register a critical-returning agent
        danger_agent = AsyncMock()
        danger_agent.name = "danger"
        danger_agent.handle = AsyncMock(
            return_value=AgentResponse(text="Danger!", safety_level="critical", tool_chain=[])
        )
        wired_orchestrator.register_agent("danger", danger_agent)

        engine = WorkflowEngine(wired_orchestrator)
        steps = [
            WorkflowStep(agent="danger", task_template={"message": "check", "user_id": 1}),
            WorkflowStep(
                agent="analytics",
                task_template={"message": "proceed", "user_id": 1},
                condition="prev.safety_level != 'critical'",
            ),
        ]

        results = await engine.execute(steps, {"user_id": 1})

        assert results[0].success is True
        assert results[1].skipped is True
        # Analytics should NOT have been called
        wired_orchestrator._agents["analytics"].handle.assert_not_called()

    @pytest.mark.asyncio
    async def test_full_flow_correlation(self, wired_orchestrator, mock_llm):
        """Full flow: classify → select → delegate → safety → response with correlation_id."""
        wired_orchestrator._classifier = MagicMock()
        wired_orchestrator._classifier.classify = AsyncMock(
            return_value=MagicMock(domain="nutrition", confidence=0.9, keywords=["comer"])
        )

        msg = make_user_message("¿Qué debo comer?", correlation_id="flow_test_123")
        response = await wired_orchestrator.route(msg)

        assert response.correlation_id == "flow_test_123"
        assert response.content["agent"] == "nutrition"
        assert "nutrition" in response.content["response"].lower() or "nutrición" in response.content["response"].lower()


# ════════════════════════════════════════════════════════════════
# GROUP 4: Performance Metrics (3 tests)
# ════════════════════════════════════════════════════════════════


class TestPerformance:
    """Measure and validate response times."""

    @pytest.mark.asyncio
    async def test_single_agent_response_time(self, wired_orchestrator, mock_llm):
        """Single agent response should be < 500ms with mock LLM."""
        wired_orchestrator._classifier = MagicMock()
        wired_orchestrator._classifier.classify = AsyncMock(
            return_value=MagicMock(domain="nutrition", confidence=0.9, keywords=["comer"])
        )

        msg = make_user_message("¿Qué debo comer?")
        start = time.monotonic()
        await wired_orchestrator.route(msg)
        elapsed_ms = (time.monotonic() - start) * 1000

        assert elapsed_ms < 500, f"Response took {elapsed_ms:.0f}ms, expected < 500ms"

    @pytest.mark.asyncio
    async def test_workflow_3step_response_time(self, wired_orchestrator):
        """3-step workflow should be < 1000ms with mock agents."""
        engine = WorkflowEngine(wired_orchestrator)
        steps = [
            WorkflowStep(agent="nutrition", task_template={"message": "step1", "user_id": 1}),
            WorkflowStep(agent="analytics", task_template={"message": "{prev.text}", "user_id": 1}),
            WorkflowStep(agent="motivation", task_template={"message": "{prev.text}", "user_id": 1}),
        ]

        start = time.monotonic()
        results = await engine.execute(steps, {"user_id": 1})
        elapsed_ms = (time.monotonic() - start) * 1000

        assert all(r.success for r in results)
        assert elapsed_ms < 1000, f"Workflow took {elapsed_ms:.0f}ms, expected < 1000ms"

    @pytest.mark.asyncio
    async def test_keyword_vs_llm_classification_latency(self, wired_orchestrator, mock_llm):
        """Keyword classification should be faster than LLM classification."""
        # Keyword path (no LLM call)
        start_kw = time.monotonic()
        result_kw = wired_orchestrator._classifier._classify_by_keywords("¿Qué debo comer hoy?")
        kw_ms = (time.monotonic() - start_kw) * 1000

        # LLM path
        mock_llm.generate = AsyncMock(return_value=make_classification_response("nutrition"))
        start_llm = time.monotonic()
        await wired_orchestrator._classifier.classify("Cuanto he avanzado esta semana")
        llm_ms = (time.monotonic() - start_llm) * 1000

        # Keyword should be faster (no network call)
        assert kw_ms < llm_ms or kw_ms < 1, f"Keyword ({kw_ms:.1f}ms) should be faster than LLM ({llm_ms:.1f}ms)"


# ════════════════════════════════════════════════════════════════
# GROUP 5: Traceability Validation (2 tests)
# ════════════════════════════════════════════════════════════════


class TestTraceability:
    """Validate structured logging and correlation ID propagation."""

    @pytest.mark.asyncio
    async def test_complete_flow_emits_all_events(self, wired_orchestrator, mock_llm):
        """route() should emit route_start, intent_classified, agent_selected, route_end."""
        wired_orchestrator._classifier = MagicMock()
        wired_orchestrator._classifier.classify = AsyncMock(
            return_value=MagicMock(domain="nutrition", confidence=0.9, keywords=["comer"])
        )

        msg = make_user_message("¿Qué debo comer?")

        with patch("src.orchestration.router._orchestration_log") as mock_log:
            await wired_orchestrator.route(msg)

            # Verify all events were emitted
            mock_log.route_start.assert_called_once()
            mock_log.intent_classified.assert_called_once()
            mock_log.agent_selected.assert_called_once()
            mock_log.route_end.assert_called_once()

            # Verify route_start data
            start_call = mock_log.route_start.call_args
            assert start_call[0][1] == 1  # user_id

            # Verify intent_classified data
            intent_call = mock_log.intent_classified.call_args
            assert intent_call[0][1] == "nutrition"  # domain

            # Verify route_end includes timing
            end_call = mock_log.route_end.call_args
            assert end_call[0][2] >= 0  # duration_ms

    @pytest.mark.asyncio
    async def test_correlation_id_consistent_across_events(self, wired_orchestrator, mock_llm):
        """Same correlation_id should appear in all log events."""
        wired_orchestrator._classifier = MagicMock()
        wired_orchestrator._classifier.classify = AsyncMock(
            return_value=MagicMock(domain="nutrition", confidence=0.9, keywords=["comer"])
        )

        msg = make_user_message("¿Qué debo comer?", correlation_id="trace_abc")

        with patch("src.orchestration.router._orchestration_log") as mock_log:
            await wired_orchestrator.route(msg)

            # All events should have the same correlation_id (first positional arg)
            start_id = mock_log.route_start.call_args[0][0]
            intent_id = mock_log.intent_classified.call_args[0][0]
            agent_id = mock_log.agent_selected.call_args[0][0]
            end_id = mock_log.route_end.call_args[0][0]

            assert start_id == intent_id == agent_id == end_id == "trace_abc"


# ════════════════════════════════════════════════════════════════
# GROUP 6: Delegation Traceability (2 tests)
# ════════════════════════════════════════════════════════════════


class TestDelegationTraceability:
    """Validate logging for agent-to-agent delegation."""

    @pytest.mark.asyncio
    async def test_delegation_logs_start_and_end(self, wired_orchestrator):
        """delegate() should emit delegation_start and delegation_end events."""
        with patch("src.orchestration.router._orchestration_log") as mock_log:
            await wired_orchestrator.delegate(
                "orchestrator", "nutrition",
                {"message": "test", "user_id": 1},
                correlation_id="del_test_01",
            )

            mock_log.delegation_start.assert_called_once()
            mock_log.delegation_end.assert_called_once()

            # Verify delegation_end includes timing (positional args)
            # delegation_end(correlation_id, from_agent, to_agent, duration_ms, success, safety_level)
            end_call = mock_log.delegation_end.call_args
            assert end_call[0][3] >= 0  # duration_ms
            assert end_call[0][4] is True  # success

    @pytest.mark.asyncio
    async def test_delegation_error_logs_failure(self, wired_orchestrator, failing_agent):
        """Failed delegation should log delegation_end with success=False."""
        wired_orchestrator.register_agent("fail", failing_agent)

        with patch("src.orchestration.router._orchestration_log") as mock_log:
            with pytest.raises(Exception):
                await wired_orchestrator.delegate(
                    "orchestrator", "fail",
                    {"message": "test", "user_id": 1},
                    correlation_id="del_fail_01",
                )

            mock_log.delegation_end.assert_called_once()
            # delegation_end(correlation_id, from_agent, to_agent, duration_ms, success)
            end_call = mock_log.delegation_end.call_args
            assert end_call[0][4] is False  # success=False
