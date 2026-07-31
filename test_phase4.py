import asyncio
from datetime import date, timedelta
from langchain_core.messages import HumanMessage

from app.database import engine, Base, AsyncSessionLocal
from app.models import User, SeniorProfile, Exercise, DailyRoutine, RoutineExercise, RoleEnum
from app.agent import wellness_agent

async def seed_database():
    """Limpia y siembra la base de datos con un escenario de fatiga severa."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSessionLocal() as session:
        # 1. Crear usuario senior
        import time
        unique_email = f"fatiga_{int(time.time())}@example.com"
        senior = User(email=unique_email, password_hash="hash", full_name="Don Pepe", role=RoleEnum.SENIOR)
        session.add(senior)
        await session.flush()
        
        # 2. Crear ejercicio en nivel 2
        exercise = Exercise(name="Sentadillas asistidas", progression_level=2)
        session.add(exercise)
        await session.flush()
        
        # 3. Crear 3 rutinas en los ultimos 3 dias con RPE=9
        for i in range(3):
            routine_date = date.today() - timedelta(days=2-i)
            routine = DailyRoutine(senior_id=senior.id, assigned_date=routine_date, status="completed")
            session.add(routine)
            await session.flush()
            
            routine_ex = RoutineExercise(routine_id=routine.id, exercise_id=exercise.id, completed=True, rpe_score=9)
            session.add(routine_ex)
            
        await session.commit()
        return senior.id, exercise.id

async def run_preventive_agent(senior_id: int):
    """Ejecuta el agente preventivo simulando un cronjob semanal o análisis."""
    print("\n[CronJob] Ejecutando análisis preventivo...")
    
    # Inyectar instrucción directa al Agente para que use sus herramientas de análisis
    query = f"Por favor, analiza mi fatiga e inactividad. Soy el usuario {senior_id}. Si encuentras fatiga severa, ajusta el nivel de mis ejercicios y envíame una alerta preventiva."
    messages = [HumanMessage(content=query)]
    
    # Invocamos el agente
    final_state = await wellness_agent.ainvoke({"messages": messages})
    response_msg = final_state["messages"][-1]
    
    print("\n[Agent Reply]:\n")
    safe_response = response_msg.content.encode('ascii', 'ignore').decode('ascii')
    print(safe_response)
    
async def verify_adjustment(exercise_id: int):
    """Verifica en base de datos si el nivel bajó de 2 a 1."""
    async with AsyncSessionLocal() as session:
        from sqlalchemy.future import select
        result = await session.execute(select(Exercise).filter(Exercise.id == exercise_id))
        exercise = result.scalars().first()
        print(f"\n[Verificación] Nivel actual del ejercicio '{exercise.name}': Nivel {exercise.progression_level}")
        if exercise.progression_level == 1:
            print("[OK] El agente redujo exitosamente el nivel de progresión.")
        else:
            print("[FAIL] El nivel de progresión no fue modificado correctamente.")

async def main():
    print("===========================================")
    print("VERIFICACIÓN FASE 4: AGENTE PREVENTIVO")
    print("===========================================")
    
    senior_id, exercise_id = await seed_database()
    print("[Seed] Base de datos preparada: Paciente con 3 días consecutivos de RPE=9 (Nivel 2).")
    
    await run_preventive_agent(senior_id)
    await verify_adjustment(exercise_id)

if __name__ == "__main__":
    asyncio.run(main())
