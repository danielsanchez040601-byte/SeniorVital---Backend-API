"""Shared fixtures for wellness tool integration tests.

Creates SQLAlchemy sessions connected to the real test PostgreSQL database.
Provides seed data fixtures for exercises, users, habits, routines, etc.
"""

import json
import uuid
import os
import pytest
from datetime import date, timedelta
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture
async def engine():
    """Create a SQLAlchemy async engine from the test DATABASE_URL."""
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:9739185@127.0.0.1:5432/seniorvital",
    )
    db_url_async = db_url.replace("postgresql://", "postgresql+asyncpg://")
    eng = create_async_engine(db_url_async, pool_size=2, max_overflow=2)
    yield eng
    await eng.dispose()


@pytest.fixture
async def db_session(engine):
    """Create an AsyncSession for tool tests."""
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
async def seed_user(db_session):
    """Insert a test user and return user_id."""
    email = f"tool_test_{uuid.uuid4().hex[:8]}@test.com"
    health = json.dumps({"fitness_level": "principiante", "medical_restrictions": []})
    prefs = json.dumps({})
    result = await db_session.execute(
        text("""INSERT INTO users (email, password, role, nombre_senior, health_profile, preferences)
                VALUES (:email, 'hash', 'senior', 'TestSenior', :hp, :pref)
                RETURNING id"""),
        {"email": email, "hp": health, "pref": prefs},
    )
    row = result.mappings().first()
    user_id = row["id"]
    await db_session.commit()
    return user_id


@pytest.fixture
async def seed_user_with_restrictions(db_session):
    """Insert a user with medical restrictions (arthritis, hypertension)."""
    email = f"tool_restrict_{uuid.uuid4().hex[:8]}@test.com"
    health = json.dumps({
        "fitness_level": "principiante",
        "medical_restrictions": ["artritis", "hipertension"],
        "conditions": ["artritis"],
    })
    prefs = json.dumps({})
    result = await db_session.execute(
        text("""INSERT INTO users (email, password, role, nombre_senior, health_profile, preferences)
                VALUES (:email, 'hash', 'senior', 'RestrictedSenior', :hp, :pref)
                RETURNING id"""),
        {"email": email, "hp": health, "pref": prefs},
    )
    row = result.mappings().first()
    user_id = row["id"]
    await db_session.commit()
    return user_id


@pytest.fixture
async def seed_exercises(db_session):
    """Insert 5 test exercises across levels 1-4 with varied contraindications."""
    exercises = [
        ("Caminata ligera", 1, "", "Camina a paso suave por 10 minutos"),
        ("Yoga suave", 2, "artritis", "Estiramientos suaves de yoga"),
        ("Pesas ligeras", 3, "hipertension", "Ejercicios con pesas de 1-2 kg"),
        ("Trote", 4, "artritis,hipertension", "Trote moderado por 20 minutos"),
        ("Natación", 1, "", "Natación en piscina climatizada"),
    ]
    for name, level, contra, desc in exercises:
        await db_session.execute(
            text("""INSERT INTO exercises (name, level, contraindications, description)
                    VALUES (:name, :level, :contra, :desc)"""),
            {"name": name, "level": level, "contra": contra, "desc": desc},
        )
    await db_session.commit()


@pytest.fixture
async def seed_habits(db_session, seed_user):
    """Insert 7 days of habit data for the test user."""
    today = date.today()
    for i in range(7):
        d = today - timedelta(days=i)
        water = 6 + (i % 3)
        sleep = 7.0 + (i % 2) * 0.5
        await db_session.execute(
            text("""INSERT INTO habits (user_id, date, water_intake_glasses, sleep_hours)
                    VALUES (:uid, :d, :water, :sleep)
                    ON CONFLICT (user_id, date) DO NOTHING"""),
            {"uid": seed_user, "d": d, "water": water, "sleep": sleep},
        )
    await db_session.commit()


@pytest.fixture
async def seed_routine(db_session, seed_user):
    """Insert today's active routine for the test user."""
    exercises_json = json.dumps([
        {"name": "Caminata", "sets": 1, "reps": 10, "duration_min": 5}
    ])
    await db_session.execute(
        text("""INSERT INTO routines (user_id, date, active, exercises, warmup, generated_by)
                VALUES (:uid, :d, true, :ex, 'Rotación de cuello', 'test')"""),
        {"uid": seed_user, "d": date.today(), "ex": exercises_json},
    )
    await db_session.commit()


@pytest.fixture
async def seed_projections(db_session, seed_user):
    """Insert weekly projections for the test user."""
    today = date.today()
    for i in range(4):
        week_start = today - timedelta(weeks=i)
        await db_session.execute(
            text("""INSERT INTO projections (user_id, week_start, insight_text, estimated_level)
                    VALUES (:uid, :ws, :insight, :level)"""),
            {"uid": seed_user, "ws": week_start, "insight": f"Insight semana {i+1}", "level": 2 + (i % 3)},
        )
    await db_session.commit()


@pytest.fixture
async def seed_workout_sessions(db_session, seed_user):
    """Insert workout sessions for progress tracking."""
    from datetime import datetime as dt, timezone
    today = date.today()
    for i in range(6):
        d = today - timedelta(days=i * 2)
        ts = dt(d.year, d.month, d.day, tzinfo=timezone.utc)
        await db_session.execute(
            text("""INSERT INTO workout_sessions (user_id, scheduled_date, completed_at)
                    VALUES (:uid, :d, :ts)"""),
            {"uid": seed_user, "d": d, "ts": ts},
        )
    await db_session.commit()
