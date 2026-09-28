"""Endpoint de chat conversacional para el Wellness Coach Agent.

Integra el ciclo iterativo ReAct (S2-05), Tool Calling dinámico (S2-04),
persistencia de contexto en PostgresMemoryStore (S2-03) y Guardrails clínicos.
"""

from datetime import datetime, timezone
import logging
import os
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.wellness.coach import WellnessCoachAgent
from src.agents.wellness.config import WellnessConfig
from src.database.database import get_db
from src.database.repositories.exercise_repository import ExerciseRepository
from src.database.repositories.user_repository import UserRepository
from src.database.schemas import ChatRequest, ChatResponse
from src.memory import MemoryStore
from src.memory.postgres_store import PostgresMemoryStore
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

router = APIRouter(prefix="/api/v1", tags=["AI Clinical Chat"])


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

    # Catálogo de herramientas especializadas para el ciclo ReAct
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


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    req: ChatRequest,
    agent: WellnessCoachAgent = Depends(get_wellness_coach_agent),
):
    """Endpoint conversacional del Wellness Coach con ReAct y memoria persistente.

    Flujo:
        1. Consulta memoria en PostgresMemoryStore.
        2. Ciclo ReAct dinámico: Thought → Action → Action Input → Observation → Final Answer.
        3. Persistencia del intercambio (user + assistant) en PostgreSQL.
        4. Aplicación de Guardrails de seguridad.
        5. Respuesta estructurada con telemetría.
    """
    start_time = time.time()
    try:
        # Invocación del ciclo ReAct con traza completa
        raw_response, trace = await agent.chat_with_trace(
            user_id=req.user_id, message=req.query
        )

        # Aplicación de Guardrails determinísticos
        secured_response = apply_guardrails(raw_response)
        is_safe = secured_response == raw_response
        elapsed_seconds = round(time.time() - start_time, 3)

        # Telemetría estructurada
        telemetry = {
            "elapsed_seconds": elapsed_seconds,
            "iterations": trace.iterations,
            "tool_calls": [
                s.action
                for s in trace.steps
                if s.action and s.action not in ("final_answer", "(direct)")
            ],
            "steps_count": len(trace.steps),
            "has_memory": agent._memory is not None,
            "mode": "react_engine",
        }

        return ChatResponse(
            response=secured_response,
            is_safe=is_safe,
            telemetry=telemetry,
        )

    except Exception as e:
        logger.error(f"Error procesando turno conversacional en ReAct: {e}")
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
                "elapsed_seconds": round(time.time() - start_time, 3),
            },
        )
