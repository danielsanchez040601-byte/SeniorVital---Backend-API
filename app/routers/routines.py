from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import date
import json
import os

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/routines",
    tags=["Routines"]
)

class GenerateRequest(BaseModel):
    user_id: int
    force: bool = False

DEFAULT_ROUTINE = {
    "exercises": [
        {"name": "Caminata ligera", "sets": 1, "reps": 10, "duration_min": 5},
        {"name": "Estiramiento de brazos", "sets": 2, "reps": 8, "duration_min": 3},
        {"name": "Respiración profunda", "sets": 1, "reps": 5, "duration_min": 2},
    ],
    "warmup": [{"name": "Rotación de cuello", "sets": 1, "reps": 5}],
}

@router.get("/today")
async def get_today_routine(user_id: int, db: AsyncSession = Depends(get_db)):
    today = date.today()
    result = await db.execute(
        select(models.DailyRoutine)
        .filter(models.DailyRoutine.senior_id == user_id)
        .filter(models.DailyRoutine.assigned_date == today)
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
    today = date.today()
    
    # Check existing
    if not req.force:
        result = await db.execute(
            select(models.DailyRoutine)
            .filter(models.DailyRoutine.senior_id == req.user_id)
            .filter(models.DailyRoutine.assigned_date == today)
        )
        existing = result.scalars().first()
        if existing:
            return {
                "routine_id": str(existing.id),
                "exercises": existing.exercises_data,
                "warmup": existing.warmup_data,
            }
            
    # Fetch Senior Profile
    profile_result = await db.execute(select(models.SeniorProfile).filter(models.SeniorProfile.user_id == req.user_id))
    profile = profile_result.scalars().first()
    
    # Prepare LLM request
    llm = ChatOpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        model=os.getenv("DEFAULT_LLM_MODEL", "inclusionai/ling-3.0-flash:free"),
        temperature=0.7
    )
    
    sys_prompt = """
    Genera una rutina de ejercicios segura para un adulto mayor.
    Responde SOLO con un JSON válido usando estrictamente este esquema, sin texto extra:
    {
      "exercises": [{"name": "nombre", "sets": 2, "reps": 10, "duration_min": 5}],
      "warmup": [{"name": "nombre", "sets": 1, "reps": 5}]
    }
    """
    
    user_prompt = "Crea una rutina básica y suave para empezar el día."
    if profile:
        user_prompt = f"Edad: {profile.age}, Nivel: {profile.fitness_level}. Restricciones: {', '.join(profile.medical_conditions)}."
    
    try:
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
    except Exception as e:
        print("Error generating routine with AI:", e)
        routine_data = DEFAULT_ROUTINE
        
    # Guardar en BD
    new_routine = models.DailyRoutine(
        senior_id=req.user_id,
        assigned_date=today,
        status=models.RoutineStatusEnum.PENDING,
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
