from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import date, datetime
from typing import List, Optional, Union
from pydantic import BaseModel, Field

try:
    from src.database.database import get_db
    from src.database.models import ExerciseRecord, DailyHabit, HealthEvent, User, SeniorProfile
except ImportError:
    try:
        from ..database.database import get_db
        from ..database.models import ExerciseRecord, DailyHabit, HealthEvent, User, SeniorProfile
    except ImportError:
        from database import get_db
        from models import ExerciseRecord, DailyHabit, HealthEvent, User, SeniorProfile

try:
    from src.agents.preventive_agent import evaluar_riesgo_fatiga
except ImportError:
    try:
        from ..agents.preventive_agent import evaluar_riesgo_fatiga
    except ImportError:
        async def evaluar_riesgo_fatiga(*args, **kwargs):
            return {"status": "normal", "alert": None}

router = APIRouter(prefix="/tracking", tags=["Tracking & Habits"])


def parse_user_id(raw_id) -> int:
    """Extrae el ID numérico de forma tolerante a UUIDs, cadenas o enteros."""
    try:
        if raw_id and "-" in str(raw_id):
            return int(str(raw_id).split("-")[-1])
        return int(raw_id or 1)
    except (ValueError, TypeError):
        return 1


class TrackRecordRequest(BaseModel):
    user_id: Union[int, str] = 1
    exercise_id: Optional[int] = None
    sets: int = Field(default=1, ge=1)
    reps: int = Field(default=10, ge=1)
    rpe: Optional[int] = Field(None, ge=1, le=10)
    felt_difficulty: Optional[str] = None
    reported_pain: Optional[str] = None


class HabitSaveRequest(BaseModel):
    user_id: Union[int, str] = 1
    date: str
    water_glasses: int = 0
    sleep_hours: float = 0.0


@router.post("/record")
async def record_exercise(req: TrackRecordRequest, db: AsyncSession = Depends(get_db)):
    """Registra la ejecución de un ejercicio, esfuerzo RPE (1-10) y evalúa alertas preventivas."""
    uid = parse_user_id(req.user_id)
    rpe_val = req.rpe or 5
    pain_val = req.reported_pain or req.felt_difficulty

    record = ExerciseRecord(
        senior_id=uid,
        exercise_id=req.exercise_id,
        sets_completed=req.sets,
        reps_completed=req.reps,
        rpe_score=rpe_val,
        reported_pain=pain_val,
        completed_at=datetime.utcnow()
    )
    db.add(record)

    # Evaluación de riesgo preventivo
    alerta = await evaluar_riesgo_fatiga(
        paciente_id=str(uid),
        rpe_score=rpe_val,
        dolor_reportado=pain_val
    )

    if rpe_val >= 8 or (pain_val and pain_val.lower() not in ["sin dolor", "ninguno", "ninguna"]):
        event = HealthEvent(
            user_id=uid,
            event_type="HIGH_FATIGUE" if rpe_val >= 8 else "PAIN_ALERT",
            payload={"rpe": rpe_val, "pain": pain_val, "alerta": alerta}
        )
        db.add(event)

    await db.commit()
    await db.refresh(record)

    return {
        "status": "success",
        "record_id": record.id,
        "senior_id": record.senior_id,
        "rpe_score": record.rpe_score,
        "preventive_alert": alerta
    }


@router.post("/habits")
async def save_habits(req: HabitSaveRequest, db: AsyncSession = Depends(get_db)):
    """Registra o actualiza los hábitos diarios (hidratación y horas de sueño) del adulto mayor."""
    uid = parse_user_id(req.user_id)
    try:
        parsed_date = date.fromisoformat(req.date)
    except Exception:
        parsed_date = date.today()

    result = await db.execute(
        select(DailyHabit)
        .filter(DailyHabit.senior_id == uid)
        .filter(DailyHabit.date == parsed_date)
    )
    habit = result.scalars().first()

    if habit:
        habit.water_glasses = req.water_glasses
        habit.sleep_hours = req.sleep_hours
    else:
        habit = DailyHabit(
            senior_id=uid,
            date=parsed_date,
            water_glasses=req.water_glasses,
            sleep_hours=req.sleep_hours
        )
        db.add(habit)

    await db.commit()
    await db.refresh(habit)

    return {
        "status": "success",
        "habit_id": habit.id,
        "senior_id": habit.senior_id,
        "date": habit.date.isoformat(),
        "water_glasses": habit.water_glasses,
        "sleep_hours": habit.sleep_hours
    }


@router.get("/habits/{user_id}/{date_str}")
async def get_habits_for_date(user_id: str, date_str: str, db: AsyncSession = Depends(get_db)):
    """Obtiene los hábitos registrados para un usuario en una fecha específica."""
    uid = parse_user_id(user_id)
    try:
        target_date = date.fromisoformat(date_str)
    except Exception:
        target_date = date.today()

    result = await db.execute(
        select(DailyHabit)
        .filter(DailyHabit.senior_id == uid)
        .filter(DailyHabit.date == target_date)
    )
    habit = result.scalars().first()

    if habit:
        return {
            "senior_id": habit.senior_id,
            "user_id": str(user_id),
            "date": habit.date.isoformat(),
            "water_glasses": habit.water_glasses,
            "sleep_hours": habit.sleep_hours
        }
    
    return {
        "senior_id": uid,
        "user_id": str(user_id),
        "date": target_date.isoformat(),
        "water_glasses": 0,
        "sleep_hours": 0.0
    }


@router.get("/habits/{user_id}")
async def get_habits_history(user_id: str, db: AsyncSession = Depends(get_db)):
    """Obtiene el historial de hábitos de los últimos 30 días para el usuario."""
    uid = parse_user_id(user_id)
    result = await db.execute(
        select(DailyHabit)
        .filter(DailyHabit.senior_id == uid)
        .order_by(DailyHabit.date.desc())
        .limit(30)
    )
    habits = result.scalars().all()

    return [
        {
            "id": h.id,
            "senior_id": h.senior_id,
            "user_id": str(user_id),
            "date": h.date.isoformat(),
            "water_glasses": h.water_glasses,
            "sleep_hours": h.sleep_hours
        }
        for h in habits
    ]
