from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/api/v1/exercises",
    tags=["Exercises (Library)"]
)

@router.post("/", response_model=schemas.ExerciseResponse, status_code=status.HTTP_201_CREATED)
async def create_exercise(exercise: schemas.ExerciseCreate, db: AsyncSession = Depends(get_db)):
    new_exercise = models.Exercise(**exercise.model_dump())
    db.add(new_exercise)
    await db.commit()
    await db.refresh(new_exercise)
    return new_exercise

@router.get("/", response_model=List[schemas.ExerciseResponse])
async def list_exercises(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Exercise).offset(skip).limit(limit))
    exercises = result.scalars().all()
    return exercises

@router.get("/{exercise_id}", response_model=schemas.ExerciseResponse)
async def get_exercise(exercise_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Exercise).filter(models.Exercise.id == exercise_id))
    exercise = result.scalars().first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return exercise
