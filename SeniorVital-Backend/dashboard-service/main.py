"""Microservicio de dashboard y analítica.

Proporciona consultas agregadas de progreso semanal,
proyecciones generadas por IA e insights históricos
para seniors y cuidadores.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()

from datetime import date, timedelta
import httpx
import duckdb
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from seniorvital_shared import get_pool, init_pool, close_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida del servicio: inicializa y cierra el pool de conexiones."""
    await init_pool(owner="dashboard")
    yield
    await close_pool(owner="dashboard")


app = FastAPI(
    title="Dashboard Service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
)


@app.get("/dashboard/progress/{user_id}")
async def get_progress(user_id: str):
    """Obtiene el resumen de progreso semanal de un usuario.

    Incluye calendario de repeticiones, tendencia de RPE,
    racha de días consecutivos y total de sesiones en la semana.

    :param user_id: ID del usuario.
    :raises HTTPException 404: Si el usuario no existe.
    :return: Progreso semanal del usuario.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT id FROM users WHERE id = $1", user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        week_ago = date.today() - timedelta(days=7)
        rows = await conn.fetch(
            """SELECT completed_at::date as day, SUM(reps) as total_reps,
                AVG(rpe) as avg_rpe
                FROM tracking
                WHERE user_id = $1 AND completed_at >= $2
                GROUP BY completed_at::date
                ORDER BY day""",
            user_id,
            week_ago,
        )

        calendar = {}
        rpe_values = []
        for r in rows:
            day_str = r["day"].isoformat()
            calendar[day_str] = r["total_reps"]
            if r["avg_rpe"]:
                rpe_values.append(round(float(r["avg_rpe"]), 1))

        today = date.today()
        streak_days = 0
        check = today
        while True:
            day_rows = await conn.fetchval(
                "SELECT COUNT(*) FROM tracking WHERE user_id = $1 AND completed_at::date = $2",
                user_id,
                check,
            )
            if day_rows and day_rows > 0:
                streak_days += 1
                check -= timedelta(days=1)
            else:
                break

        total_sessions = await conn.fetchval(
            "SELECT COUNT(DISTINCT completed_at::date) FROM tracking WHERE user_id = $1 AND completed_at >= $2",
            user_id,
            week_ago,
        )

        return {
            "calendar": calendar,
            "avg_rpe_trend": rpe_values,
            "streak_days": streak_days,
            "total_sessions_week": total_sessions or 0,
        }


@app.get("/dashboard/projection/{user_id}")
async def get_projection(user_id: str):
    """Obtiene la última proyección generada por el agente semanal.

    :param user_id: ID del usuario.
    :return: Proyección más reciente o null si no existe.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM projections WHERE user_id = $1 ORDER BY week_start DESC LIMIT 1",
            user_id,
        )
        if not row:
            return {"projection": None}
        return {
            "projection": {
                "id": str(row["id"]),
                "week_start": row["week_start"].isoformat(),
                "insight_text": row["insight_text"],
                "estimated_level": row["estimated_level"],
            }
        }


@app.get("/dashboard/insights/{user_id}")
async def get_insights(user_id: str):
    """Obtiene el historial de insights generados para un usuario.

    :param user_id: ID del usuario.
    :return: Lista de hasta 10 insights ordenados por semana descendente.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM projections WHERE user_id = $1 ORDER BY week_start DESC LIMIT 10",
            user_id,
        )
        return [
            {
                "id": str(r["id"]),
                "week_start": r["week_start"].isoformat(),
                "insight_text": r["insight_text"],
                "estimated_level": r["estimated_level"],
            }
            for r in rows
        ]


import json
from datetime import datetime

def format_last_sync(dt):
    if not dt:
        return "Nunca"
    now = datetime.now()
    diff = now.date() - dt.date()
    if diff.days == 0:
        return f"Hoy, {dt.strftime('%H:%M')}"
    elif diff.days == 1:
        return f"Ayer, {dt.strftime('%H:%M')}"
    else:
        return f"Hace {diff.days} días"


@app.get("/dashboard/residents")
async def get_residents_clinical_summary():
    """Obtiene el resumen de todos los residentes para el panel de administración."""
    pool = await get_pool()
    residents = []
    async with pool.acquire() as conn:
        users = await conn.fetch("SELECT id, email, profile FROM users WHERE role = 'senior'")
        
        for u in users:
            user_id = u["id"]
            email = u["email"]
            profile = json.loads(u["profile"]) if isinstance(u["profile"], str) else (u["profile"] or {})
            
            # Map names and units to keep consistency with the demo dashboard
            if email == "senior@vital.com":
                name = "Eleanor Rigby"
                unit = "Unidad 2B"
            else:
                name = email.split("@")[0].title().replace(".", " ")
                unit = profile.get("preferred_schedule", "Unidad 1A")
                if unit in ("mañana", "tarde", "noche"):
                    unit = "Unidad 1A"
            
            # Get last sync
            last_sync_row = await conn.fetchval(
                "SELECT completed_at FROM tracking WHERE user_id = $1 ORDER BY completed_at DESC LIMIT 1",
                user_id
            )
            
            # Get tracking in the last 48 hours for RPE
            forty_eight_hours_ago = datetime.utcnow() - timedelta(hours=48)
            recent_rpes = await conn.fetch(
                "SELECT rpe FROM tracking WHERE user_id = $1 AND completed_at >= $2",
                user_id,
                forty_eight_hours_ago
            )
            
            # Determine status
            status = "stable"
            status_text = "Rutina Estable"
            
            if not last_sync_row:
                status = "offline"
                status_text = "Dispositivo Desconectado"
            elif (datetime.utcnow() - last_sync_row).days >= 4:
                status = "offline"
                status_text = "Dispositivo Desconectado"
            else:
                # Check for high fatigue in the last 48h
                rpe_values = [r["rpe"] for r in recent_rpes if r["rpe"] is not None]
                if any(rpe >= 8 for rpe in rpe_values):
                    status = "review"
                    status_text = "Revisión Recomendada"
                elif any(rpe >= 6 for rpe in rpe_values):
                    status = "observation"
                    status_text = "Observación Sugerida"
            
            residents.append({
                "id": str(user_id),
                "name": name,
                "unit": unit,
                "lastSync": format_last_sync(last_sync_row),
                "status": status,
                "statusText": status_text,
                "email": email,
                "profile": profile
            })
            
    return residents


@app.post("/dashboard/analyze/{user_id}")
async def run_live_weekly_analysis(user_id: str):
    """Ejecuta el análisis semanal clínico con Ollama a demanda para un residente."""
    DUCKDB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "seniorvital_analytics.duckdb")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "google/gemma-4-31b:free")
    OLLAMA_MODEL = DEFAULT_LLM_MODEL
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT email, profile FROM users WHERE id = $1", user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Resident not found")
            
        week_start = date.today() - timedelta(days=date.today().weekday())
        
        # Conectar a DuckDB para leer weekly_progress
        # Si falla o no hay datos en DuckDB, usaremos valores por defecto basados en tracking real
        avg_rpe = 5.0
        total_exercises = 0
        streak_days = 0
        
        try:
            con = duckdb.connect(DUCKDB_PATH)
            weekly = con.execute(
                """SELECT AVG(avg_rpe) as avg_rpe, SUM(total_exercises) as total_exercises,
                    MAX(streak_days) as streak_days
                    FROM weekly_progress
                    WHERE user_id = ? AND week_start = ?""",
                [user_id, week_start.isoformat()],
            ).fetchone()
            con.close()
            
            if weekly and weekly[0] is not None:
                avg_rpe = float(weekly[0])
                total_exercises = int(weekly[1] or 0)
                streak_days = int(weekly[2] or 0)
        except Exception as e:
            # Fallback: consultar PostgreSQL directamente
            print(f"Error querying DuckDB, attempting PostgreSQL fallback: {e}")
            pg_weekly = await conn.fetchrow(
                """SELECT AVG(rpe) as avg_rpe, COUNT(*) as total_exercises
                   FROM tracking
                   WHERE user_id = $1 AND completed_at >= $2""",
                user_id,
                datetime.utcnow() - timedelta(days=7)
            )
            if pg_weekly and pg_weekly["total_exercises"] > 0:
                avg_rpe = float(pg_weekly["avg_rpe"]) if pg_weekly["avg_rpe"] else 5.0
                total_exercises = int(pg_weekly["total_exercises"])
                streak_days = 1 # simplificado
        
        # Consultar Ollama para generar el insight
        prompt = f"""
        Analiza el progreso de movilidad del adulto mayor (ID: {user_id}):
        - RPE promedio (esfuerzo): {avg_rpe}
        - Total ejercicios esta semana: {total_exercises}
        - Racha de consistencia (días): {streak_days}

        Genera un insight clínico breve (máximo 2 oraciones) y un nivel de condición física estimado (1-4).
        Responde SOLO con JSON válido con esta estructura:
        {{"insight_text": "string", "estimated_level": int}}
        """
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
                )
                resp.raise_for_status()
                insight_data = json.loads(resp.json()["response"])
        except Exception as e:
            print(f"Ollama generation failed: {e}")
            insight_data = {
                "insight_text": "Se mantiene un ritmo de entrenamiento moderado y estable. Continuar con la rutina programada.",
                "estimated_level": 1
            }

        # Guardar en projections (PostgreSQL)
        await conn.execute(
            """INSERT INTO projections (user_id, week_start, insight_text, estimated_level)
               VALUES ($1, $2, $3, $4)""",
            user_id,
            week_start,
            insight_data.get("insight_text", ""),
            insight_data.get("estimated_level", 1)
        )
        
        return {
            "week_start": week_start.isoformat(),
            "insight_text": insight_data.get("insight_text", ""),
            "estimated_level": insight_data.get("estimated_level", 1)
        }


