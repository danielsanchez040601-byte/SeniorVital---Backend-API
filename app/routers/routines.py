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
    
    routine_data = None
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    # 1. Prioridad: Google AI Studio Directo (Gemini 3.6 Flash / Ultrarrápido y sin intermediarios)
    if gemini_key:
        import httpx
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
                            print(f"Rutina generada con éxito usando Google AI Studio ({gem_model})")
                            break
            except Exception as gem_err:
                print(f"Aviso Google AI Studio ({gem_model}): {gem_err}")

    # 2. Respaldo: OpenRouter Multimodelo
    if (not routine_data or "exercises" not in routine_data) and os.getenv("OPENROUTER_API_KEY"):
        preferred_model = os.getenv("DEFAULT_LLM_MODEL", "google/gemma-4-31b-it:free")
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
                    api_key=os.getenv("OPENROUTER_API_KEY"),
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
