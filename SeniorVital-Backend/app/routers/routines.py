from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import date
import json
import os
import httpx
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..database import get_db
from ..models import DailyRoutine, SeniorProfile, RoutineStatusEnum
from ..schemas import GenerateRequest, DailyRoutineResponse
from ..config import settings

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
async def get_today_routine(user_id: int, db: AsyncSession = Depends(get_db)):
    """Obtiene la rutina asignada para el día de hoy."""
    today = date.today()
    result = await db.execute(
        select(DailyRoutine)
        .filter(DailyRoutine.senior_id == user_id)
        .filter(DailyRoutine.assigned_date == today)
    )
    routine = result.scalars().first()
    if not routine:
        raise HTTPException(status_code=404, detail="No routine for today")
    
    return {
        "id": routine.id,
        "user_id": routine.senior_id,
        "date": routine.assigned_date.isoformat(),
        "exercises": routine.exercises_data,
        "warmup": routine.warmup_data,
    }


@router.post("/generate")
async def generate_routine(req: GenerateRequest, db: AsyncSession = Depends(get_db)):
    """Genera una rutina clínica adaptada con IA (Google AI Studio / OpenRouter / Fallback)."""
    today = date.today()

    # Si no se fuerza la regeneración, retornamos la rutina existente
    if not req.force:
        result = await db.execute(
            select(DailyRoutine)
            .filter(DailyRoutine.senior_id == req.user_id)
            .filter(DailyRoutine.assigned_date == today)
        )
        existing = result.scalars().first()
        if existing:
            return {
                "routine_id": str(existing.id),
                "exercises": existing.exercises_data,
                "warmup": existing.warmup_data,
            }

    # Obtener perfil del adulto mayor
    profile_result = await db.execute(
        select(SeniorProfile).filter(SeniorProfile.user_id == req.user_id)
    )
    profile = profile_result.scalars().first()

    sys_prompt = """
    Genera una rutina de ejercicios segura para un adulto mayor.
    Responde SOLO con un JSON válido usando estrictamente este esquema:
    {
      "exercises": [{"name": "nombre", "sets": 2, "reps": 10, "duration_min": 5}],
      "warmup": [{"name": "nombre", "sets": 1, "reps": 5}]
    }
    """
    user_prompt = "Crea una rutina básica y suave para empezar el día."
    if profile:
        user_prompt = f"Edad: {profile.age or 70}, Nivel: {profile.fitness_level}. Restricciones: {', '.join(profile.medical_conditions)}."

    routine_data = None
    gemini_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY

    # 1. Prioridad: Google AI Studio Directo (Gemini 3.6 Flash / Ultrarrápido)
    if gemini_key:
        for gem_model in ["gemini-3.6-flash", "gemini-flash-latest"]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{gem_model}:generateContent?key={gemini_key}"
                full_prompt = f"{sys_prompt}\n\nDatos del Adulto Mayor:\n{user_prompt}"
                payload = {
                    "contents": [{"parts": [{"text": full_prompt}]}],
                    "generationConfig": {"response_mime_type": "application/json"}
                }
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                        routine_data = json.loads(raw_text)
                        if routine_data and "exercises" in routine_data:
                            print(f"Rutina generada con Google AI Studio ({gem_model})")
                            break
            except Exception as gem_err:
                print(f"Aviso Google AI Studio ({gem_model}): {gem_err}")

    # 2. Respaldo: OpenRouter Multimodelo
    if (not routine_data or "exercises" not in routine_data) and settings.OPENROUTER_API_KEY:
        preferred_model = settings.DEFAULT_LLM_MODEL
        if preferred_model == "google/gemma-4-31b:free":
            preferred_model = "google/gemma-4-31b-it:free"

        candidate_models = [
            preferred_model,
            "google/gemma-4-26b-a4b-it:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "mistralai/mistral-7b-instruct:free"
        ]
        for model_name in candidate_models:
            try:
                llm = ChatOpenAI(
                    api_key=settings.OPENROUTER_API_KEY,
                    base_url="https://openrouter.ai/api/v1",
                    model=model_name,
                    temperature=0.7,
                    default_headers={
                        "HTTP-Referer": "https://seniorvital-backend.onrender.com",
                        "X-Title": "SeniorVital"
                    }
                )
                resp = await llm.ainvoke([
                    SystemMessage(content=sys_prompt),
                    HumanMessage(content=user_prompt)
                ])
                content = resp.content.strip()
                if content.startswith("```json"):
                    content = content.split("```json")[1].split("```")[0].strip()
                elif content.startswith("```"):
                    content = content.split("```")[1].split("```")[0].strip()
                    
                routine_data = json.loads(content)
                if routine_data and "exercises" in routine_data:
                    print(f"Rutina generada con modelo OpenRouter: {model_name}")
                    break
            except Exception as model_err:
                print(f"Aviso OpenRouter ({model_name}): {model_err}")

    if not routine_data or "exercises" not in routine_data:
        print("Usando rutina preventiva clínica por defecto (Fallback seguro).")
        routine_data = DEFAULT_ROUTINE

    # Guardar en Base de Datos
    new_routine = DailyRoutine(
        senior_id=req.user_id,
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
