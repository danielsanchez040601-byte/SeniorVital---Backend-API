"""SQLAlchemy ORM models — maps existing PostgreSQL tables.

These models map the EXISTING schema (14 tables). Only the 3 tables
needed for S2-01 are defined here. Add others as needed.
"""

from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Integer, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


from enum import Enum


class RoleEnum(str, Enum):
    SENIOR = "senior"
    CAREGIVER = "caregiver"
    ADMIN = "admin"


class RoutineStatusEnum(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class Base(DeclarativeBase):
    pass


class User(Base):
    """Mapping de la tabla users."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    role: Mapped[str]  # CHECK: senior | caregiver | admin
    profile: Mapped[dict] = mapped_column(JSON, default={})
    health_profile: Mapped[dict] = mapped_column(JSON, default={})
    preferences: Mapped[dict] = mapped_column(JSON, default={})
    nombre_senior: Mapped[str | None] = mapped_column(Text, nullable=True)
    nombre_cuidador: Mapped[str | None] = mapped_column(Text, nullable=True)
    linked_senior_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Exercise(Base):
    """Mapping de la tabla exercises."""

    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    level: Mapped[int]  # CHECK: 1-4
    contraindications: Mapped[str] = mapped_column(Text, default="")
    video_url: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Routine(Base):
    """Mapping de la tabla routines."""

    __tablename__ = "routines"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int]  # FK -> users.id (not declared here to avoid circular deps)
    date: Mapped[date]
    active: Mapped[bool] = mapped_column(default=True)
    exercises: Mapped[dict] = mapped_column(JSON, default=[])
    warmup: Mapped[str] = mapped_column(Text, default="")
    generated_by: Mapped[str] = mapped_column(Text, default="ollama")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
