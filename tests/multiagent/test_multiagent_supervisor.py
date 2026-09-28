"""Tests unitarios y de integración para el Supervisor Multiagente y Agentes Especializados.
Evalúa AnalyticsAgent, MotivationAgent, QAArchitectAgent y MultiAgentOrchestrator.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.multi_agent_orchestrator import (
    AnalyticsAgent,
    MotivationAgent,
    QAArchitectAgent,
    MultiAgentOrchestrator,
)


# ---------------------------------------------------------------------------
# 1. PRUEBAS DE QA ARCHITECT AGENT (ISO/IEC 25010)
# ---------------------------------------------------------------------------
def test_qa_agent_approves_safe_response():
    qa = QAArchitectAgent()
    safe_text = "Realice caminatas suaves de 15 minutos en terreno plano y mantenga una hidratación constante."
    result = qa.audit_response(safe_text)
    assert result["is_approved"] is True
    assert len(result["violations"]) == 0
    assert "ISO/IEC 25010" in result["standards_evaluated"]


def test_qa_agent_blocks_prohibited_medication():
    qa = QAArchitectAgent()
    unsafe_text = "Para calmar el dolor en su rodilla, tome ibuprofeno en dosis de 400mg cada 8 horas."
    result = qa.audit_response(unsafe_text)
    assert result["is_approved"] is False
    assert any("ibuprofeno" in v.lower() for v in result["violations"])


def test_qa_agent_blocks_dangerous_biomechanics():
    qa = QAArchitectAgent()
    unsafe_text = "Para fortalecer sus piernas, realice saltos pliométricos enérgicos en el jardín."
    result = qa.audit_response(unsafe_text)
    assert result["is_approved"] is False
    assert any("saltos" in v.lower() or "pliometria" in v.lower() for v in result["violations"])


# ---------------------------------------------------------------------------
# 2. PRUEBAS DE MOTIVATION AGENT (WCAG 2.1 AA)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_motivation_agent_high_adherence():
    agent = MotivationAgent()
    res = await agent.generate_encouragement(user_name="Carmen", adherence=85.0, risk_level="GREEN")
    assert "Carmen" in res["motivational_message"]
    assert "constancia" in res["motivational_message"].lower() or "admirable" in res["motivational_message"].lower()
    assert res["agent"] == "MotivationAgent"
    assert res["elapsed_ms"] >= 0


@pytest.mark.asyncio
async def test_motivation_agent_red_risk_empathy():
    agent = MotivationAgent()
    res = await agent.generate_encouragement(user_name="Roberto", adherence=40.0, risk_level="RED")
    assert "cuerpo" in res["motivational_message"].lower() or "descanso" in res["motivational_message"].lower()


# ---------------------------------------------------------------------------
# 3. PRUEBAS DE ANALYTICS AGENT (Supabase PostgreSQL / JSONB)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_analytics_agent_fallback_on_db_exception():
    agent = AnalyticsAgent()
    with patch("app.agents.multi_agent_orchestrator.AsyncSessionLocal", side_effect=Exception("Database connection timeout")):
        res = await agent.analyze_patient_progression(user_id=123)
        assert res["agent"] == "AnalyticsAgent"
        assert res["status"] == "FALLBACK"
        assert res["risk_level"] == "GREEN"
        assert res["adherence_rate"] > 0


# ---------------------------------------------------------------------------
# 4. PRUEBAS DEL ORQUESTADOR SUPERVISOR
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_orchestrator_delegates_and_aggregates_traces():
    orchestrator = MultiAgentOrchestrator()

    mock_coach_res = {
        "response": "Le sugiero ejercicios de movilidad articular sentado para cuidar sus rodillas.",
        "reasoning_trace": [{"thought": "Verifico seguridad", "action": "consultar_restricciones"}],
        "elapsed_time": 0.25
    }

    with patch.object(orchestrator.wellness_coach, "execute_react_cycle", new=AsyncMock(return_value=mock_coach_res)):
        result = await orchestrator.orchestrate_request(user_id="1", query="¿Qué ejercicios puedo hacer hoy?")
        
        assert "trace_id" in result
        assert result["qa_status"] == "APPROVED"
        assert "final_response" in result
        assert len(result["execution_traces"]) >= 4
        assert result["total_elapsed_ms"] > 0
        assert "adherence" in result["analytics_summary"]


@pytest.mark.asyncio
async def test_orchestrator_sanitizes_unsafe_coach_response():
    orchestrator = MultiAgentOrchestrator()

    unsafe_coach_res = {
        "response": "Haga saltos de tijera vigorosos y tome paracetamol si siente dolor.",
        "reasoning_trace": [],
        "elapsed_time": 0.1
    }

    with patch.object(orchestrator.wellness_coach, "execute_react_cycle", new=AsyncMock(return_value=unsafe_coach_res)):
        result = await orchestrator.orchestrate_request(user_id="1", query="Tengo dolor")
        
        assert result["qa_status"] == "SANITIZED"
        assert "seguridad" in result["final_response"].lower()
        assert "paracetamol" not in result["final_response"].lower()
