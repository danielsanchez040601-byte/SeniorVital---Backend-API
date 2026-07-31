from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime, date
from .models import RoleEnum, RoutineStatusEnum

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: RoleEnum = RoleEnum.SENIOR

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Senior Profile Schemas ---
class SeniorProfileBase(BaseModel):
    age: Optional[int] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    medical_conditions: List[str] = Field(default_factory=list)
    fitness_level: int = Field(default=1, ge=1, le=3)
    equipment_available: List[str] = Field(default_factory=list)
    objectives: Optional[str] = None

class SeniorProfileCreate(SeniorProfileBase):
    user_id: int

class SeniorProfileResponse(SeniorProfileBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

# --- Exercise Schemas ---
class ExerciseBase(BaseModel):
    name: str
    description: Optional[str] = None
    video_url: Optional[str] = None
    progression_level: int = Field(default=1, ge=1, le=4)
    contraindications: List[str] = Field(default_factory=list)
    target_muscles: List[str] = Field(default_factory=list)

class ExerciseCreate(ExerciseBase):
    pass

class ExerciseResponse(ExerciseBase):
    id: int

    class Config:
        from_attributes = True

# --- Routine & Habits Schemas ---
class RoutineExerciseBase(BaseModel):
    exercise_id: int
    order: int = 1
    completed: bool = False
    rpe_score: Optional[int] = Field(None, ge=1, le=10)

class RoutineExerciseCreate(RoutineExerciseBase):
    pass

class RoutineExerciseResponse(RoutineExerciseBase):
    id: int
    routine_id: int
    exercise: Optional[ExerciseResponse] = None

    class Config:
        from_attributes = True

class DailyRoutineBase(BaseModel):
    senior_id: int
    assigned_date: date
    status: RoutineStatusEnum = RoutineStatusEnum.PENDING

class DailyRoutineCreate(DailyRoutineBase):
    pass

class DailyRoutineResponse(DailyRoutineBase):
    id: int
    exercises: List[RoutineExerciseResponse] = []

    class Config:
        from_attributes = True

class DailyHabitBase(BaseModel):
    senior_id: int
    date: date
    water_glasses: int = 0
    sleep_hours: float = 0.0

class DailyHabitCreate(DailyHabitBase):
    pass

class DailyHabitResponse(DailyHabitBase):
    id: int

    class Config:
        from_attributes = True
