import asyncio
from langchain_core.tools import tool
from app.vectorstore import buscar_memorias_paciente, ingestar_memoria_paciente

@tool
def consultar_historial_medico(paciente_id: str, query: str) -> str:
    """Ejecuta búsquedas semánticas en el historial médico (PGVector) para extraer síntomas previos o memorias.
    Es obligatorio pasar el paciente_id del usuario y la pregunta/tema a buscar (query)."""
    # En LangChain las tools sincrónicas con async internals deben ejecutarse cuidadosamente.
    # Usaremos asyncio.run u obtendremos el loop (mejor usar funciones sync puras o llamar al await si es un tool asíncrono, pero para simplificar, llamamos a la función sincrónica si es posible).
    # wait, buscar_memorias_paciente es async, podemos hacer un loop temporal.
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Estamos dentro de un event loop (LangGraph async), deberíamos haber hecho la tool asíncrona,
        # pero para mantenerlo robusto a entornos sync/async, devolveremos una corrutina a LangChain
        # Ah! A partir de Langchain podemos definir la función asíncrona directamente.
        pass
        
# Refactorizando para que las herramientas sean asíncronas de forma nativa en LangChain
@tool
async def consultar_historial_medico(paciente_id: str, query: str) -> str:
    """Consulta el historial médico del paciente buscando información semánticamente relevante a la query.
    Útil para saber qué condiciones médicas tiene el paciente o sus antecedentes."""
    resultados = await buscar_memorias_paciente(paciente_id, query)
    if not resultados:
        return "No se encontraron memorias previas relevantes para este paciente."
    return "\n".join(resultados)

@tool
async def registrar_evento_salud(paciente_id: str, síntoma_o_evento: str) -> str:
    """Guarda síntomas, medicamentos u observaciones claves en el historial médico del paciente.
    Usa esto para recordar proactivamente dolores reportados, evolución o diagnósticos comentados."""
    exito = await ingestar_memoria_paciente(paciente_id, síntoma_o_evento)
    if exito:
        return "Evento de salud registrado con éxito en la memoria del paciente."
    else:
        return "Hubo un error al registrar el evento en la memoria."

from app.database import AsyncSessionLocal
from sqlalchemy.future import select
from app.models import DailyRoutine, RoutineExercise, Exercise
import datetime

@tool
async def analizar_fatiga_inactividad(senior_id: int) -> str:
    """Consulta la base de datos SQL para detectar si el paciente está inactivo (sin rutinas completadas) o si está estancado por fatiga severa (RPE >= 8 en los últimos días).
    Devuelve un reporte claro sobre el estado del paciente."""
    async with AsyncSessionLocal() as db:
        # Check inactividad
        result_inactivo = await db.execute(
            select(DailyRoutine)
            .filter(DailyRoutine.senior_id == senior_id)
            .order_by(DailyRoutine.assigned_date.desc())
            .limit(5)
        )
        rutinas = result_inactivo.scalars().all()
        
        if not rutinas:
            return "ALERTA INACTIVIDAD: El usuario no tiene rutinas asignadas ni completadas recientemente."
            
        rutinas_completadas = [r for r in rutinas if r.status.value == "completed"]
        if not rutinas_completadas and len(rutinas) >= 4:
            return "ALERTA INACTIVIDAD: El usuario lleva 4 o más rutinas sin completar (riesgo de abandono)."
            
        # Check fatiga (RPE alto)
        # Obtenemos los últimos 3 RoutineExercise de este usuario
        # Filtramos por las rutinas del usuario
        result_rpe = await db.execute(
            select(RoutineExercise)
            .join(DailyRoutine, RoutineExercise.routine_id == DailyRoutine.id)
            .filter(DailyRoutine.senior_id == senior_id)
            .filter(RoutineExercise.rpe_score != None)
            .order_by(DailyRoutine.assigned_date.desc())
            .limit(3)
        )
        exercises_rpe = result_rpe.scalars().all()
        
        if len(exercises_rpe) == 3 and all(e.rpe_score >= 8 for e in exercises_rpe):
            ejercicio_id = exercises_rpe[0].exercise_id
            return f"FATIGA SEVERA: El paciente reportó un esfuerzo excesivo (RPE >= 8) en los últimos 3 días. Se recomienda bajar el nivel de progresión del ejercicio {ejercicio_id}."
            
        return "ESTADO NORMAL: El paciente está activo y sin fatiga severa detectada."

@tool
async def ajustar_nivel_ejercicio(senior_id: int, exercise_id: int, nuevo_nivel: int) -> str:
    """Disminuye o aumenta el nivel de progresión de un ejercicio en la base de datos (por ejemplo, para adaptar a un usuario con fatiga)."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Exercise).filter(Exercise.id == exercise_id))
        exercise = result.scalars().first()
        if not exercise:
            return "Error: Ejercicio no encontrado."
            
        old_level = exercise.progression_level
        exercise.progression_level = nuevo_nivel
        await db.commit()
        return f"Éxito: El ejercicio '{exercise.name}' pasó del nivel {old_level} al nivel {nuevo_nivel} de forma segura."

@tool
async def enviar_alerta_preventiva(senior_id: int, mensaje: str) -> str:
    """Envía una notificación push motivacional o alerta empática al adulto mayor o a su cuidador."""
    # Simulación de Firebase Cloud Messaging (FCM)
    safe_mensaje = mensaje.encode('ascii', 'ignore').decode('ascii')
    print(f"\n[FCM PUSH NOTIFICATION a senior_id={senior_id}]: {safe_mensaje}\n")
    return f"Notificación enviada correctamente: {mensaje}"
