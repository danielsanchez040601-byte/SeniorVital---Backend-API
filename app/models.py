from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum, JSON, Float, Date
from sqlalchemy.orm import relationship
from datetime import datetime, date
import enum
from .database import Base

class RoleEnum(str, enum.Enum):
    SENIOR = "senior"
    CAREGIVER = "caregiver"
    ADMIN = "admin"

class RoutineStatusEnum(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.SENIOR, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    senior_profile = relationship("SeniorProfile", back_populates="user", uselist=False)
    # Caregivers this senior has:
    caregivers = relationship("CaregiverLink", foreign_keys="CaregiverLink.senior_id", back_populates="senior")
    # Seniors this caregiver manages:
    seniors_managed = relationship("CaregiverLink", foreign_keys="CaregiverLink.caregiver_id", back_populates="caregiver")
    routines = relationship("DailyRoutine", back_populates="senior")
    habits = relationship("DailyHabit", back_populates="senior")

class SeniorProfile(Base):
    __tablename__ = "senior_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Antropometría
    age = Column(Integer)
    weight_kg = Column(Float)
    height_cm = Column(Float)
    
    # Estado y Restricciones (lista de strings, ej: ["artritis", "hipertension"])
    medical_conditions = Column(JSON, default=list)
    fitness_level = Column(Integer, default=1) # 1: Sedentario, 2: Ligero, 3: Activo
    equipment_available = Column(JSON, default=list)
    objectives = Column(String)
    
    user = relationship("User", back_populates="senior_profile")

class CaregiverLink(Base):
    __tablename__ = "caregiver_links"

    id = Column(Integer, primary_key=True, index=True)
    caregiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    senior_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    caregiver = relationship("User", foreign_keys=[caregiver_id], back_populates="seniors_managed")
    senior = relationship("User", foreign_keys=[senior_id], back_populates="caregivers")

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    video_url = Column(String)
    progression_level = Column(Integer, default=1) # 1 a 4
    
    # Contraindicaciones médicas obligatorias (ej. "artritis_rodilla")
    contraindications = Column(JSON, default=list)
    
    # Músculos estimulados para mapa anatómico 2D
    target_muscles = Column(JSON, default=list) 

class DailyRoutine(Base):
    __tablename__ = "daily_routines"

    id = Column(Integer, primary_key=True, index=True)
    senior_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_date = Column(Date, default=date.today)
    status = Column(Enum(RoutineStatusEnum), default=RoutineStatusEnum.PENDING)
    
    exercises_data = Column(JSON, default=list)
    warmup_data = Column(JSON, default=list)
    
    senior = relationship("User", back_populates="routines")
    exercises = relationship("RoutineExercise", back_populates="routine")

class RoutineExercise(Base):
    __tablename__ = "routine_exercises"

    id = Column(Integer, primary_key=True, index=True)
    routine_id = Column(Integer, ForeignKey("daily_routines.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    
    order = Column(Integer, default=1)
    completed = Column(Boolean, default=False)
    
    # RPE Escala 1-10 capturada post-ejercicio
    rpe_score = Column(Integer, nullable=True) 

    routine = relationship("DailyRoutine", back_populates="exercises")
    exercise = relationship("Exercise")

class DailyHabit(Base):
    __tablename__ = "daily_habits"

    id = Column(Integer, primary_key=True, index=True)
    senior_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, default=date.today)
    
    water_glasses = Column(Integer, default=0)
    sleep_hours = Column(Float, default=0.0)

    senior = relationship("User", back_populates="habits")
