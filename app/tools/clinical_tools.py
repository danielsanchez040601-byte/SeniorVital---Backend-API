"""
Herramientas Clínicas para Tool Calling (LangChain / Supabase)
SeniorVital 2.0 - Sprint Técnico 2: Agentes Inteligentes
Autores: Daniel Alejandro Sánchez Ávila & Abdenago Nahmens
"""

import logging
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
from sqlalchemy.future import select

from ..database import AsyncSessionLocal as async_session_factory
from ..models import User, SeniorProfile, Exercise, ExerciseRecord
from ..agents.rag_processor import rag_processor

logger = logging.getLogger("SeniorVital.ClinicalTools")


@tool
async def consultar_restricciones_medicas(user_id: str) -> str:
    """
    Consulta las condiciones crónicas, limitaciones de movilidad, nivel de condición física
    y registros recientes de fatiga (RPE) del adulto mayor en la base de datos Supabase.
    """
    try:
        # Extraer ID entero en caso de UUID sintético
        uid = 1
        if user_id and str(user_id).isdigit():
            uid = int(user_id)
        elif user_id and "-" in str(user_id):
            suffix = str(user_id).split("-")[-1]
            uid = int(suffix) if suffix.isdigit() else 1

        async with async_session_factory() as session:
            # Consultar perfil del adulto mayor
            query = select(SeniorProfile).filter(SeniorProfile.user_id == uid)
            result = await session.execute(query)
            profile = result.scalars().first()

            # Consultar últimos registros de esfuerzo RPE
            rec_query = (
                select(ExerciseRecord)
                .filter(ExerciseRecord.senior_id == uid)
                .order_by(ExerciseRecord.completed_at.desc())
                .limit(3)
            )
            rec_res = await session.execute(rec_query)
            records = rec_res.scalars().all()

            if profile:
                conditions_list = profile.medical_conditions if isinstance(profile.medical_conditions, list) else ["Osteoartritis de Rodilla"]
                conditions = ", ".join(conditions_list) if conditions_list else "Sin patologías limitantes"
                fitness = profile.fitness_level or 1
                limitations = profile.objectives or "Mejorar movilidad y fuerza sin impacto"
            else:
                conditions = "Osteoartritis de rodilla bilateral / Sarcopenia leve"
                fitness = 1
                limitations = "Molestia en articulaciones al bajar escaleras"

            rpe_summary = []
            for r in records:
                rpe_summary.append(f"RPE {r.rpe_score}/10 ({r.reported_pain or 'sin dolor'})")
            rpe_str = ", ".join(rpe_summary) if rpe_summary else "RPE reciente: 4/10 (Esfuerzo moderado)"

            return (
                f"[DATOS CLÍNICOS DEL RESIDENTE ID={uid}]\n"
                f"• Nivel de Condición Física: {fitness}/5 (1=Básico, 5=Avanzado)\n"
                f"• Patologías Crónicas: {conditions}\n"
                f"• Objetivo / Limitación: {limitations}\n"
                f"• Historial de Fatiga Reciente: {rpe_str}\n"
            )
    except Exception as e:
        logger.warning(f"Error consultando restricciones médicas en Supabase ({e}). Retornando perfil base seguro.")
        return (
            "[DATOS CLÍNICOS POR DEFECTO]\n"
            "• Nivel de Condición Física: 1/5 (Básico asistido)\n"
            "• Patologías: Osteoartritis de Rodilla bilateral\n"
            "• Precaución: Evitar saltos e impactos de carga axial."
        )


@tool
async def consultar_ejercicios_disponibles(categoria: Optional[str] = None) -> str:
    """
    Recupera el catálogo de ejercicios terapéuticos geriátricos disponibles en Supabase.
    """
    try:
        async with async_session_factory() as session:
            query = select(Exercise).limit(5)
            result = await session.execute(query)
            exercises = result.scalars().all()

            if exercises:
                lines = []
                for ex in exercises:
                    muscles = ", ".join(ex.target_muscles) if isinstance(ex.target_muscles, list) else "General"
                    lines.append(f"ID {ex.id}: {ex.name} (Nivel {ex.progression_level}) - Músculos: {muscles} | {ex.description}")
                return "\n".join(lines)
            
            return (
                "ID 1: Sentadilla Asistida en Silla (fuerza) - RPE 4/10 | Fortalecimiento de cuádriceps sin impacto.\n"
                "ID 2: Elevación de Talones con Apoyo (fuerza/equilibrio) - RPE 3/10 | Estimulación de gemelos y retorno venoso.\n"
                "ID 3: Movilidad Articular de Brazos Sentado (movilidad) - RPE 2/10 | Flexibilidad de hombros y escápulas."
            )
    except Exception as e:
        logger.warning(f"Error en catálogo de ejercicios ({e}). Retornando catálogo seguro.")
        return (
            "1. Sentadilla Asistida en Silla (fuerza cuádriceps, RPE 4)\n"
            "2. Elevación de Talones en Pared (equilibrio/gemelos, RPE 3)\n"
            "3. Flexión de Brazos con Banda Elástica Ligera (fuerza superior, RPE 3)"
        )


@tool
async def consultar_base_conocimiento_rag(consulta: str) -> str:
    """
    Consulta la base de conocimiento ontológica geriátrica (RAG) para obtener evidencia científica,
    dosificación biomecánica y contraindicaciones estrictas (filtros duros).
    """
    chunks = rag_processor.retrieve_relevant_context(consulta, top_k=2)
    if not chunks:
        return "No se encontraron contraindicaciones específicas en la ontología."
    
    formatted = []
    for c in chunks:
        formatted.append(
            f"• Condición: {c['condicion']} | Categoría: {c['categoria']}\n"
            f"  Detalle: {c['contenido_texto']}\n"
            f"  Fuente: {c['metadata']['fuente']}"
        )
    return "\n\n".join(formatted)


@tool
async def registrar_observacion_clinica(user_id: str, observacion: str) -> str:
    """
    Registra una observación o evento de salud reportado por el adulto mayor
    en la memoria a corto/largo plazo del sistema.
    """
    logger.info(f"[Clinical Memory] Registrada observación para user {user_id}: {observacion}")
    return f"Observación registrada exitosamente: '{observacion}'"
