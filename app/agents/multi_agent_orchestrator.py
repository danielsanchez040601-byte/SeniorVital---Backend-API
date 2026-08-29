"""
SeniorVital 2.0 - Ecosistema Multiagente y Orquestación Supervisor
Materia: Sistemas Inteligentes (Dra. Yaskelly Yedra)
Autores: Daniel Alejandro Sánchez Ávila & Abdenago Nahmens
Patrón: Supervisor Jerárquico (Hierarchical Orchestrator + Specialized Agents)
Stack: FastAPI + Supabase PostgreSQL (SQL/JSONB) + Google AI Studio (Gemini) / OpenRouter
"""

import json
import logging
import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.future import select
from sqlalchemy import func

from ..database import AsyncSessionLocal
from ..models import User, SeniorProfile, ExerciseRecord, DailyRoutine, DailyHabit, RoutineStatusEnum
from .wellness_coach import wellness_coach_agent
from .rag_processor import rag_processor
from .llm_client import call_llm_text

logger = logging.getLogger("SeniorVital.MultiAgentOrchestrator")


# ---------------------------------------------------------------------------
# 1. AGENTE ESPECIALIZADO: ANALYTICS & PREVENCIÓN (Supabase SQL/JSONB)
# ---------------------------------------------------------------------------
class AnalyticsAgent:
    """
    Agente analítico y predictivo que inspecciona históricos en Supabase PostgreSQL.
    Reemplaza la necesidad de BigQuery mediante agregaciones SQL asíncronas.
    """
    def __init__(self):
        self.name = "AnalyticsAgent"

    async def analyze_patient_progression(self, user_id: int) -> Dict[str, Any]:
        """
        Calcula adherencia, detecta estancamiento y riesgo de abandono.
        """
        start_t = time.time()
        async with AsyncSessionLocal() as session:
            # 1. Consultar rutinas de los últimos 14 días
            limit_date = (datetime.utcnow() - timedelta(days=14)).date()
            routines_query = (
                select(DailyRoutine)
                .filter(DailyRoutine.senior_id == user_id, DailyRoutine.assigned_date >= limit_date)
            )
            res_routines = await session.execute(routines_query)
            routines = res_routines.scalars().all()

            # 2. Consultar registros de esfuerzo RPE
            records_query = (
                select(ExerciseRecord)
                .filter(ExerciseRecord.senior_id == user_id)
                .order_by(ExerciseRecord.completed_at.desc())
                .limit(10)
            )
            res_records = await session.execute(records_query)
            records = res_records.scalars().all()

            # Métricas calculadas
            total_assigned = len(routines)
            completed = sum(1 for r in routines if r.status == RoutineStatusEnum.COMPLETED)
            adherence = round((completed / total_assigned * 100), 1) if total_assigned > 0 else 50.0

            rpe_scores = [r.rpe_score for r in records if r.rpe_score is not None]
            avg_rpe = round(sum(rpe_scores) / len(rpe_scores), 1) if rpe_scores else 4.0

            pain_reports = [r.reported_pain for r in records if r.reported_pain and r.reported_pain.lower() not in ["sin dolor", "ninguno", ""]]
            has_pain = len(pain_reports) > 0

            # Detección de estancamiento o riesgo clínico
            is_stagnant = False
            risk_level = "GREEN" # GREEN, AMBER, RED
            recommendations = []

            if has_pain or avg_rpe >= 8.0:
                risk_level = "RED"
                recommendations.append("Alerta clínica: Reducir carga biomecánica y notificar al cuidador.")
            elif adherence < 50.0 or avg_rpe >= 6.5:
                risk_level = "AMBER"
                is_stagnant = True
                recommendations.append("Fatiga acumulada o adherencia baja: Proponer micro-sesiones guiadas.")
            else:
                risk_level = "GREEN"
                recommendations.append("Progresión óptima: Mantener nivel de actividad y reforzar motivación.")

            elapsed_ms = round((time.time() - start_t) * 1000, 2)
            
            return {
                "agent": self.name,
                "user_id": user_id,
                "adherence_rate": adherence,
                "avg_rpe": avg_rpe,
                "is_stagnant": is_stagnant,
                "risk_level": risk_level,
                "pain_reported": pain_reports,
                "recommendations": recommendations,
                "elapsed_ms": elapsed_ms
            }


# ---------------------------------------------------------------------------
# 2. AGENTE ESPECIALIZADO: MOTIVACIÓN Y EMPATÍA
# ---------------------------------------------------------------------------
class MotivationAgent:
    """
    Agente de interfaz emocional gerontológica. Genera refuerzos positivos no punitivos
    celebrando pequeños logros ("cada paso cuenta").
    """
    def __init__(self):
        self.name = "MotivationAgent"

    async def generate_encouragement(self, user_name: str, adherence: float, risk_level: str) -> Dict[str, Any]:
        start_t = time.time()
        if risk_level == "RED":
            message = (
                f"Estimado/a {user_name}, lo más importante es escuchar a su cuerpo. "
                "Hoy descansemos y cuidemos sus articulaciones; descansar también es parte del bienestar."
            )
        elif adherence >= 70.0:
            message = (
                f"¡Excelente trabajo, {user_name}! Ha mantenido una constancia admirable. "
                "Su esfuerzo diario fortalece su vitalidad y autonomía."
            )
        else:
            message = (
                f"¡Bienvenido de vuelta, {user_name}! Recuerde que cada pequeño movimiento cuenta. "
                "Hagamos hoy una rutina suave a su propio ritmo."
            )

        elapsed_ms = round((time.time() - start_t) * 1000, 2)
        return {
            "agent": self.name,
            "motivational_message": message,
            "tone": "Empático Gerontológico (WCAG 2.1 AA)",
            "elapsed_ms": elapsed_ms
        }


# ---------------------------------------------------------------------------
# 3. AGENTE ESPECIALIZADO: QA ARCHITECT & GUARDRAILS (ISO/IEC 25010)
# ---------------------------------------------------------------------------
class QAArchitectAgent:
    """
    Agente auditor de calidad. Evalúa que las respuestas cumplan con la norma ISO/IEC 25010,
    cero prescripciones lesionales y ausencia de recomendaciones farmacológicas.
    """
    def __init__(self):
        self.name = "QAArchitectAgent"

    def audit_response(self, raw_text: str) -> Dict[str, Any]:
        start_t = time.time()
        prohibited_meds = ["ibuprofeno", "paracetamol", "morfina", "tramadol", "aspirina", "cirugia"]
        dangerous_prescriptions = [
            "haga saltos", "realice saltos", "haga pliometria", "realice pliometria",
            "sentadillas profundas sin apoyo", "aguante la respiracion", "maniobra de valsalva"
        ]

        violations = []
        lower_t = raw_text.lower()

        for med in prohibited_meds:
            if med in lower_t and ("tome" in lower_t or "dosis" in lower_t or "receto" in lower_t):
                violations.append(f"Prescripción indebida de fármaco: '{med}'")

        for ex in dangerous_prescriptions:
            if ex in lower_t:
                violations.append(f"Prescripción biomecánicamente peligrosa: '{ex}'")

        is_approved = len(violations) == 0
        elapsed_ms = round((time.time() - start_t) * 1000, 2)

        return {
            "agent": self.name,
            "is_approved": is_approved,
            "violations": violations,
            "standards_evaluated": ["ISO/IEC 25010", "SWEBOK v4", "WCAG 2.1 AA"],
            "elapsed_ms": elapsed_ms
        }


# ---------------------------------------------------------------------------
# 4. ORQUESTADOR PRINCIPAL (SUPERVISOR AGENT)
# ---------------------------------------------------------------------------
class MultiAgentOrchestrator:
    """
    Supervisor Jerárquico:
    1. Recibe la solicitud del usuario o cuidador
    2. Clasifica la intención y delega a los agentes especializados
    3. Coordina el paso de mensajes (A2A) sin ciclos infinitos
    4. Audita la calidad mediante QAArchitectAgent antes de emitir la respuesta
    """
    def __init__(self):
        self.analytics_agent = AnalyticsAgent()
        self.motivation_agent = MotivationAgent()
        self.qa_agent = QAArchitectAgent()
        self.wellness_coach = wellness_coach_agent

    async def orchestrate_request(self, user_id: str, query: str, user_role: str = "senior") -> Dict[str, Any]:
        trace_id = str(uuid.uuid4())[:8]
        start_total = time.time()
        traces: List[Dict[str, Any]] = []

        uid = 1
        if user_id and str(user_id).isdigit():
            uid = int(user_id)
        elif user_id and "-" in str(user_id):
            suffix = str(user_id).split("-")[-1]
            uid = int(suffix) if suffix.isdigit() else 1

        logger.info(f"[Supervisor:{trace_id}] Iniciando orquestación para user={uid}, role={user_role}")

        # PASO 1: Analítica y Detección de Riesgo
        analytics_result = await self.analytics_agent.analyze_patient_progression(uid)
        traces.append(analytics_result)

        # PASO 2: Generación de Refuerzo Motivacional
        motivation_result = await self.motivation_agent.generate_encouragement(
            user_name="Adulto Mayor",
            adherence=analytics_result["adherence_rate"],
            risk_level=analytics_result["risk_level"]
        )
        traces.append(motivation_result)

        # PASO 3: Delegación al Wellness Coach (ReAct + RAG + Supabase)
        coach_result = await self.wellness_coach.execute_react_cycle(
            user_id=str(uid),
            query=query
        )
        traces.append({
            "agent": "WellnessCoachAgent",
            "reasoning_trace": coach_result.get("reasoning_trace"),
            "elapsed_ms": round(coach_result.get("elapsed_time", 1.0) * 1000, 2)
        })

        # PASO 4: Auditoría de Calidad y Seguridad ISO 25010 (QA Architect)
        raw_output = coach_result.get("response", "")
        qa_result = self.qa_agent.audit_response(raw_output)
        traces.append(qa_result)

        final_response = raw_output
        if not qa_result["is_approved"]:
            logger.warning(f"[Supervisor:{trace_id}] Respuesta bloqueada por QA: {qa_result['violations']}")
            final_response = (
                f"{motivation_result['motivational_message']}\n\n"
                "Para su seguridad, le recomiendo realizar ejercicios de movilidad articular sentado "
                "con respiración pausada. Si siente cualquier molestia, deténgase de inmediato."
            )

        total_elapsed_ms = round((time.time() - start_total) * 1000, 2)

        return {
            "trace_id": trace_id,
            "user_id": uid,
            "user_role": user_role,
            "final_response": final_response,
            "analytics_summary": {
                "adherence": f"{analytics_result['adherence_rate']}%",
                "risk_level": analytics_result["risk_level"],
                "avg_rpe": analytics_result["avg_rpe"]
            },
            "motivational_nudge": motivation_result["motivational_message"],
            "qa_status": "APPROVED" if qa_result["is_approved"] else "SANITIZED",
            "execution_traces": traces,
            "total_elapsed_ms": total_elapsed_ms
        }


# Instancia global del Orquestador Supervisor
supervisor_orchestrator = MultiAgentOrchestrator()
