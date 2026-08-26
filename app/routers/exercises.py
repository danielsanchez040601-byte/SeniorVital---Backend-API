from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from ..database import get_db
from ..models import Exercise
from ..schemas import ExerciseCreate, ExerciseResponse

router = APIRouter(prefix="/api/v1/exercises", tags=["Exercises (Library)"])


@router.get("/", response_model=List[ExerciseResponse])
async def list_exercises(
    skip: int = 0, 
    limit: int = 100, 
    level: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Obtiene el catálogo de ejercicios clínicos filtrado por nivel de progresión."""
    query = select(Exercise)
    if level is not None:
        query = query.filter(Exercise.progression_level == level)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    exercises = result.scalars().all()
    
    # Fallback con catálogo base si la tabla estuviera vacía en primera carga
    if not exercises and skip == 0:
        return [
            ExerciseResponse(
                id=1,
                name="Sentadillas asistidas en silla",
                description="Fortalecimiento de cuádriceps con apoyo seguro.",
                video_url=None,
                progression_level=1,
                contraindications=["gonartrosis_severa"],
                target_muscles=["cuádriceps", "glúteos"]
            ),
            ExerciseResponse(
                id=2,
                name="Elevación de talones de pie con apoyo",
                description="Estimulación de gemelos y retorno venoso.",
                video_url=None,
                progression_level=1,
                contraindications=[],
                target_muscles=["pantorrillas"]
            ),
            ExerciseResponse(
                id=3,
                name="Marcha estática con apoyo ligero",
                description="Activación cardiovascular suave y equilibrio.",
                video_url=None,
                progression_level=2,
                contraindications=["inestabilidad_severa"],
                target_muscles=["cardiovascular", "flexores_cadera"]
            )
        ]
    return exercises


@router.get("/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(exercise_id: int, db: AsyncSession = Depends(get_db)):
    """Obtiene el detalle de un ejercicio por su ID."""
    result = await db.execute(select(Exercise).filter(Exercise.id == exercise_id))
    ex = result.scalars().first()
    if not ex:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado.")
    return ex


@router.post("/", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
async def create_exercise(exercise_in: ExerciseCreate, db: AsyncSession = Depends(get_db)):
    """Registra un nuevo ejercicio clínico en la biblioteca."""
    new_ex = Exercise(**exercise_in.dict())
    db.add(new_ex)
    await db.commit()
    await db.refresh(new_ex)
    return new_ex
