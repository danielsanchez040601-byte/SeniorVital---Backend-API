from pydantic import BaseModel, Field
try:
    from pydantic import EmailStr
except ImportError:
    EmailStr = str

from typing import List, Optional
from datetime import datetime, date
from .models import RoleEnum, RoutineStatusEnum


# --- User & Auth Schemas ---
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


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Optional[UserResponse] = None


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


# --- Routine Schemas ---
class GenerateRequest(BaseModel):
    user_id: int
    force: bool = False


class DailyRoutineBase(BaseModel):
    senior_id: int
    assigned_date: date
    status: RoutineStatusEnum = RoutineStatusEnum.PENDING
    exercises_data: list = Field(default_factory=list)
    warmup_data: list = Field(default_factory=list)


class DailyRoutineResponse(DailyRoutineBase):
    id: int

    class Config:
        from_attributes = True


# --- Exercise Tracking & RPE Schemas ---
class ExerciseRecordCreate(BaseModel):
    user_id: int
    exercise_id: Optional[int] = None
    sets_completed: int = Field(default=1, ge=1)
    reps_completed: int = Field(default=10, ge=1)
    rpe_score: int = Field(..., ge=1, le=10, description="Escala RPE Borg 1 a 10")
    reported_pain: Optional[str] = Field(None, description="Zona articular de dolor reportada")


class ExerciseRecordResponse(BaseModel):
    id: int
    senior_id: int
    exercise_id: Optional[int]
    sets_completed: int
    reps_completed: int
    rpe_score: int
    reported_pain: Optional[str]
    completed_at: datetime

    class Config:
        from_attributes = True


# --- Habit Schemas ---
class DailyHabitBase(BaseModel):
    senior_id: int
    date: date
    water_glasses: int = 0
    sleep_hours: float = 0.0


class DailyHabitResponse(DailyHabitBase):
    id: int

    class Config:
        from_attributes = True


# --- AI Chat & RAG Schemas ---
class ChatRequest(BaseModel):
    user_id: str
    query: str


class ChatResponse(BaseModel):
    response: str
    is_safe: bool
