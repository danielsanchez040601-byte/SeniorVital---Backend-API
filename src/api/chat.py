"""Endpoint de chat conversacional multiagente para SeniorVital.

Implementa el patrón Supervisor Centralizado (S3-01, S3-02, S3-04):
- Clasificación de intención del usuario.
- Despacho y delegación dinámica hacia agentes especializados (NutritionAgent, WellnessCoachAgent).
- Propagación de correlation_id para trazabilidad de extremo a extremo.
- Persistencia de contexto en PostgresMemoryStore y guardrails clínicos.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
import os
import time
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.nutrition import (
    ClinicalDietaryCheckTool,
    NutritionAgent,
    NutritionCalculatorTool,
)
from src.agents.nutrition.adapter import NutritionAgentAdapter
from src.agents.wellness.coach import WellnessCoachAgent
from src.agents.wellness.coach_adapter import WellnessCoachAgentAdapter
from src.agents.wellness.config import WellnessConfig
from src.database.database import get_db
from src.database.repositories.exercise_repository import ExerciseRepository
from src.database.repositories.user_repository import UserRepository
from src.database.schemas import ChatRequest, ChatResponse
from src.memory import MemoryStore
from src.memory.postgres_store import PostgresMemoryStore
from src.orchestration.dispatch import DispatchRequest, DispatchResponse
from src.orchestration.router import OrchestratorAgent
from src.services.llm import LLMService
from src.services.user_data import UserDataService
from src.tools.wellness.exercise_catalog import ExerciseCatalogTool
from src.tools.wellness.get_habits import GetHabitsTool
from src.tools.wellness.get_progress import GetProgressTool
from src.tools.wellness.get_routine import GetRoutineTool
from src.tools.wellness.log_habit import LogHabitTool
from src.tools.wellness.rag_search import RAGSearchTool
from src.tools.wellness.safety_check import SafetyCheckTool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["AI Clinical Multi-Agent Chat"])


def apply_guardrails(text: str) -> str:
    """Capa de seguridad clínica determinística en Python puro."""
    prohibited_terms = ["ibuprofeno", "paracetamol", "morfina", "tramadol", "cirugia", "cirugía"]
    lower_text = text.lower()
    for term in prohibited_terms:
        if term in lower_text:
            return (
                "Como asistente de bienestar, no estoy autorizado para recomendar medicamentos o dosis. "
                "Por favor, consulte a su médico o fisioterapeuta de cabecera."
            )
    return text


async def get_memory_store() -> Optional[MemoryStore]:
    """Obtiene la instancia de PostgresMemoryStore conectada al pool compartido de PostgreSQL."""
    try:
        from seniorvital_shared import get_pool
        pool = await get_pool()
        if pool:
            return PostgresMemoryStore(pool)
    except Exception as e:
        logger.warning(
            f"PostgresMemoryStore no disponible mediante pool compartido: {e}. "
            "El agente operará en modo efímero o mock para este turno."
        )
    return None


async def get_wellness_coach_agent(
    db: AsyncSession = Depends(get_db),
    memory_store: Optional[MemoryStore] = Depends(get_memory_store),
) -> WellnessCoachAgent:
    """Construye e inyecta la instancia canónica de WellnessCoachAgent con herramientas y memoria."""
    user_repo = UserRepository(db)
    exercise_repo = ExerciseRepository(db)
    user_data_service = UserDataService(user_repo, exercise_repo)

    config = WellnessConfig(max_react_iterations=3)
    llm_service = LLMService(
        base_url=config.llm_url,
        model=config.llm_model,
        timeout=config.llm_timeout,
    )

    tools = [
        SafetyCheckTool(db),
        ExerciseCatalogTool(db),
        RAGSearchTool(None),
        LogHabitTool(db),
        GetHabitsTool(db),
        GetProgressTool(db),
        GetRoutineTool(db),
    ]

    return WellnessCoachAgent(
        llm=llm_service,
        user_data=user_data_service,
        tools=tools,
        memory_store=memory_store,
        config=config,
    )


async def get_nutrition_agent(
    db: AsyncSession = Depends(get_db),
    memory_store: Optional[MemoryStore] = Depends(get_memory_store),
) -> NutritionAgent:
    """Construye e inyecta la instancia del agente especializado en Nutrición (Team 5)."""
    user_repo = UserRepository(db)
    exercise_repo = ExerciseRepository(db)
    user_data_service = UserDataService(user_repo, exercise_repo)

    config = WellnessConfig(max_react_iterations=3)
    llm_service = LLMService(
        base_url=config.llm_url,
        model=config.llm_model,
        timeout=config.llm_timeout,
    )

    tools = [
        NutritionCalculatorTool(),
        ClinicalDietaryCheckTool(),
        SafetyCheckTool(db),
        RAGSearchTool(None),
    ]

    return NutritionAgent(
        llm=llm_service,
        user_data=user_data_service,
        tools=tools,
        memory_store=memory_store,
        config=config,
    )


async def get_orchestrator_agent(
    coach: WellnessCoachAgent = Depends(get_wellness_coach_agent),
    nutrition: NutritionAgent = Depends(get_nutrition_agent),
) -> OrchestratorAgent:
    """Construye e inyecta el OrchestratorAgent bajo el patrón Supervisor Centralizado."""
    llm_service = getattr(coach, "_llm", None) or LLMService()
    orchestrator = OrchestratorAgent(llm=llm_service)

    coach_adapter = WellnessCoachAgentAdapter(coach)
    nutrition_adapter = NutritionAgentAdapter(nutrition)

    orchestrator.register_agent("nutrition", nutrition_adapter)
    orchestrator.register_agent("wellness_coach", coach_adapter)
    orchestrator.register_agent("general", coach_adapter)
    orchestrator.register_agent("safety", coach_adapter)
    orchestrator.register_agent("analytics", coach_adapter)
    orchestrator.set_fallback(coach_adapter)

    return orchestrator


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    req: ChatRequest,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator_agent),
):
    """Endpoint conversacional orquestado bajo el patrón Supervisor Centralizado.

    Flujo:
        1. Generación de correlation_id para trazabilidad de extremo a extremo.
        2. Construcción de DispatchRequest formal con contexto de sesión.
        3. Clasificación de intención y delegación dinámica (NutritionAgent vs WellnessCoachAgent).
        4. Verificación de seguridad y guardrails clínicos.
        5. Respuesta estructurada con telemetría unificada.
    """
    start_time = time.time()
    correlation_id = str(uuid.uuid4())[:12]

    try:
        dispatch_req = DispatchRequest(
            user_id=req.user_id,
            message=req.query,
            correlation_id=correlation_id,
            context={"user_id": req.user_id},
        )

        dispatch_res = await orchestrator.dispatch(dispatch_req)

        secured_response = apply_guardrails(dispatch_res.text)
        is_safe = (not dispatch_res.blocked) and (secured_response == dispatch_res.text)
        elapsed_seconds = round(time.time() - start_time, 3)

        tool_calls = dispatch_res.tool_chain or []
        iterations = (
            dispatch_res.metadata.get("iterations", 1)
            if dispatch_res.metadata
            else 1
        )
        steps_count = (
            dispatch_res.metadata.get("steps_count", len(tool_calls))
            if dispatch_res.metadata
            else len(tool_calls)
        )

        telemetry = {
            "elapsed_seconds": elapsed_seconds,
            "correlation_id": correlation_id,
            "agent_selected": dispatch_res.agent,
            "intent": dispatch_res.intent,
            "safety_level": dispatch_res.safety_level,
            "blocked": dispatch_res.blocked,
            "tool_calls": tool_calls,
            "steps_count": steps_count,
            "iterations": iterations,
            "has_memory": True,
            "mode": "react_engine" if dispatch_res.agent in ("wellness_coach", "coach") else "supervisor_orchestration",
        }

        return ChatResponse(
            response=secured_response,
            is_safe=is_safe,
            telemetry=telemetry,
        )

    except Exception as e:
        logger.error(f"Error procesando turno conversacional en Supervisor: {e}")
        fallback_response = (
            "Como su asistente de SeniorVital, le recomiendo descansar, "
            "mantenerse hidratado y realizar estiramientos ligeros de bajo impacto. "
            "Ante cualquier molestia persistente, por favor notifíquelo a su cuidador o médico."
        )
        return ChatResponse(
            response=fallback_response,
            is_safe=True,
            telemetry={
                "error": str(e),
                "mode": "fallback_graceful",
                "correlation_id": correlation_id,
                "elapsed_seconds": round(time.time() - start_time, 3),
            },
        )
