from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import date
from typing import Optional, Union, Dict, Any, List
import json
import os
import httpx
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..database import get_db
from ..models import DailyRoutine, SeniorProfile, RoutineStatusEnum
from ..schemas import GenerateRequest, DailyRoutineResponse
from ..config import settings
from ..agents.llm_client import call_llm_json

router = APIRouter(prefix="/routines", tags=["Routines"])

DEFAULT_ROUTINE = {
    "exercises": [
        {"name": "Caminata ligera asistida", "sets": 1, "reps": 10, "duration_min": 5},
        {"name": "Estiramiento de hombros y brazos", "sets": 2, "reps": 8, "duration_min": 3},
        {"name": "Respiración diafragmática profunda", "sets": 1, "reps": 5, "duration_min": 2},
    ],
    "warmup": [{"name": "Rotación suave de tobillos y cuello", "sets": 1, "reps": 5}],
}


@router.get("/today")
async def get_today_routine(user_id: Optional[str] = "1", db: AsyncSession = Depends(get_db)):
    """Obtiene la rutina asignada para el día de hoy con soporte tolerante a UUIDs y strings."""
    today = date.today()
    try:
        if user_id and "-" in str(user_id):
            parsed_id = int(str(user_id).split("-")[-1])
        else:
            parsed_id = int(user_id or 1)
    except (ValueError, TypeError):
        parsed_id = 1

    result = await db.execute(
        select(DailyRoutine)
        .filter(DailyRoutine.senior_id == parsed_id)
        .filter(DailyRoutine.assigned_date == today)
    )
    routine = result.scalars().first()
    if not routine:
        # Retornar rutina clínica por defecto para evitar pantallas en blanco
        return {
            "id": 1,
            "routine_id": "1",
            "user_id": str(user_id),
            "date": today.isoformat(),
            "exercises": DEFAULT_ROUTINE.get("exercises", []),
            "warmup": DEFAULT_ROUTINE.get("warmup", []),
            "status": "pending"
        }
    
    return {
        "id": routine.id,
        "routine_id": str(routine.id),
        "user_id": str(user_id),
        "date": routine.assigned_date.isoformat(),
        "exercises": routine.exercises_data,
        "warmup": routine.warmup_data,
        "status": routine.status.value if hasattr(routine.status, 'value') else "pending"
    }


@router.post("/generate")
async def generate_routine(req: GenerateRequest, db: AsyncSession = Depends(get_db)):
    """Genera una rutina clínica adaptada con IA (Google AI Studio / OpenRouter / Fallback)."""
    today = date.today()

    # Parsear ID de usuario de forma segura (admite int, str, "demo-user", etc.)
    raw_uid = req.user_id if req.user_id is not None else (req.senior_id or 1)
    try:
        target_user_id = int(raw_uid)
    except (ValueError, TypeError):
        target_user_id = 1

    # Si no se fuerza la regeneración, retornamos la rutina existente
    if not req.force:
        result = await db.execute(
            select(DailyRoutine)
            .filter(DailyRoutine.senior_id == target_user_id)
            .filter(DailyRoutine.assigned_date == today)
        )
        existing = result.scalars().first()
        if existing:
            return {
                "routine_id": str(existing.id),
                "exercises": existing.exercises_data,
                "warmup": existing.warmup_data,
            }

    # 1. Consultar perfil clínico del adulto mayor desde la base de datos (PostgreSQL/Supabase)
    profile_result = await db.execute(
        select(SeniorProfile).filter(SeniorProfile.user_id == target_user_id)
    )
    profile = profile_result.scalars().first()

    # System Prompt Clínico Oficial — Coach SeniorVital
    sys_prompt = """
    Eres el "Coach SeniorVital", un asistente clínico de inteligencia artificial especializado en bienestar y actividad física para adultos mayores de 60 años.
    Tu misión es diseñar una rutina de ejercicios diaria altamente personalizada, segura y preventiva.

    REGLAS CLÍNICAS GERONTOLÓGICAS OBLIGATORIAS:
    1. SEGURIDAD ANTE TODO: Si el paciente tiene dolor articular o nivel sedentario (Nivel 1), prescribe ejercicios sentados en silla o con apoyo fijo. Nunca prescribas saltos ni cargas de alto impacto.
    2. ESTRUCTURA OBLIGATORIA: Toda rutina debe tener una fase de calentamiento articular ('warmup') de 3-5 minutos y de 3 a 4 ejercicios principales ('exercises').
    3. PROGRESIÓN SEGURA: Series de 1 a 3, con 6 a 12 repeticiones o duraciones de 2 a 5 minutos, con descansos adecuados.
    4. TONO Y LENGUAJE: Nombres claros y descriptivos (ej. "Sentadillas asistidas en silla con apoyo", "Rotación articular de tobillos").

    RESPONDE EXCLUSIVAMENTE CON UN OBJETO JSON VÁLIDO CON ESTA ESTRUCTURA EXACTA:
    {
      "warmup": [
        {"name": "Rotación suave de cuello y hombros", "sets": 1, "reps": 5, "duration_min": 2}
      ],
      "exercises": [
        {"name": "Sentadillas asistidas en silla", "sets": 2, "reps": 8, "duration_min": 4, "description": "Levantarse y sentarse con apoyo firme.", "target_muscles": ["cuádriceps", "glúteos"]},
        {"name": "Elevación de talones con apoyo", "sets": 2, "reps": 10, "duration_min": 3, "description": "Ponerse de puntillas sosteniéndose del respaldo.", "target_muscles": ["pantorrillas"]},
        {"name": "Respiración diafragmática profunda", "sets": 1, "reps": 5, "duration_min": 2, "description": "Inspirar profundamente por la nariz y exhalar despacio.", "target_muscles": ["respiratorio"]}
      ]
    }
    """

    user_prompt = "Prescribe una rutina segura para el día de hoy."
    if profile:
        conditions = ', '.join(profile.medical_conditions) if profile.medical_conditions else "Ninguna reportada"
        user_prompt = (
            f"Perfil del Adulto Mayor:\n"
            f"- Edad: {profile.age or 70} años\n"
            f"- Nivel Funcional: Nivel {profile.fitness_level} (1: Sedentario/Silla, 2: Movilidad Ligera, 3: Activo)\n"
            f"- Condiciones Clínicas / Dolores: {conditions}\n"
            f"- Objetivos: {profile.objectives or 'Mejorar movilidad y prevenir caídas'}"
        )

    # Generación con IA usando sistema de Fallback Resiliente
    routine_data = await call_llm_json(
        system_prompt=sys_prompt,
        user_prompt=user_prompt,
        timeout=14.0
    )

    if not routine_data or "exercises" not in routine_data:
        print("🛡️ [Routines] Activando rutina preventiva clínica por defecto (Degradación Elegante).")
        routine_data = DEFAULT_ROUTINE

    # Guardar en Base de Datos
    new_routine = DailyRoutine(
        senior_id=target_user_id,
        assigned_date=today,
        status=RoutineStatusEnum.PENDING,
        exercises_data=routine_data.get("exercises", []),
        warmup_data=routine_data.get("warmup", [])
    )
    db.add(new_routine)
    await db.commit()
    await db.refresh(new_routine)

    return {
        "routine_id": str(new_routine.id),
        "exercises": new_routine.exercises_data,
        "warmup": new_routine.warmup_data,
    }
