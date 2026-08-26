"""Inicializador y sembrador de la base de datos de Senior Vital.

Crea la base de datos senior_vital, ejecuta los scripts SQL de esquema
y migración, adapta la tabla de hábitos y crea usuarios y ejercicios de demo.
"""

import os
import sys
import json
import asyncio
from passlib.hash import bcrypt
import asyncpg
from dotenv import load_dotenv

# Asegurar que el directorio raíz está en el path para cargar dotenv
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
load_dotenv()

# Obtener DATABASE_URL
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:Nika@localhost:5432/senior_vital"
)

# Parsear DSN para conectar a base de datos por defecto 'postgres'
# E.g., postgresql://username:password@host:port/database
def get_base_dsn(dsn, new_db="postgres"):
    # Reemplazar la base de datos de destino al final del DSN
    parts = dsn.rsplit("/", 1)
    if len(parts) == 2:
        return f"{parts[0]}/{new_db}"
    return dsn


async def init_database():
    print("Iniciando inicialización de base de datos...")
    
    # 1. Crear base de datos si no existe
    base_dsn = get_base_dsn(DATABASE_URL, "postgres")
    try:
        conn = await asyncpg.connect(dsn=base_dsn)
        try:
            # Verificar si existe senior_vital
            exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = 'senior_vital')"
            )
            if not exists:
                # CREATE DATABASE no se puede ejecutar en transacción
                await conn.execute("CREATE DATABASE senior_vital")
                print("Base de datos 'senior_vital' creada con éxito.")
            else:
                print("La base de datos 'senior_vital' ya existe.")
        finally:
            await conn.close()
    except Exception as e:
        print(f"Error al verificar/crear la base de datos: {e}")
        # Si falla, intentamos continuar por si ya existe y no tenemos permisos para listar/crear
    
    # 2. Conectar a senior_vital y crear tablas
    print("Conectando a 'senior_vital' para aplicar esquema...")
    conn = await asyncpg.connect(dsn=DATABASE_URL)
    try:
        # Cargar init_db.sql
        init_sql_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "init_db.sql")
        if os.path.exists(init_sql_path):
            with open(init_sql_path, "r", encoding="utf-8") as f:
                init_sql = f.read()
            # Ejecutar init_db.sql
            # Separar por sentencias para evitar fallos si algunas cosas ya existen
            # Nota: asyncpg permite ejecutar bloques completos
            await conn.execute(init_sql)
            print("Esquema básico 'init_db.sql' aplicado.")
        else:
            print("ADVERTENCIA: No se encontró 'init_db.sql'.")

        # Cargar scripts/migrations.sql
        migrations_sql_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "scripts", "migrations.sql"
        )
        if os.path.exists(migrations_sql_path):
            with open(migrations_sql_path, "r", encoding="utf-8") as f:
                migrations_sql = f.read()
            await conn.execute(migrations_sql)
            print("Migraciones 'migrations.sql' aplicadas.")
        else:
            print("ADVERTENCIA: No se encontró 'migrations.sql'.")

        # 3. Alterar tabla habits para añadir columnas de caminata y medicación
        print("Modificando tabla 'habits' para soporte completo de UI...")
        await conn.execute("""
            ALTER TABLE habits 
            ADD COLUMN IF NOT EXISTS walking_minutes INT DEFAULT 0,
            ADD COLUMN IF NOT EXISTS meds_taken BOOLEAN DEFAULT NULL
        """)
        print("Tabla 'habits' modificada con éxito.")

        # 4. Sembrar (seed) ejercicios por defecto en la base de datos
        print("Sembrando ejercicios en el catálogo...")
        default_exercises = [
            {
                "name": "Estiramientos Suaves de Mañana",
                "level": 1,
                "contraindications": [],
                "video_url": "http://localhost:8002/storage/videos/morning_stretches.mp4"
            },
            {
                "name": "Caminata ligera",
                "level": 1,
                "contraindications": [],
                "video_url": ""
            },
            {
                "name": "Respiración profunda",
                "level": 1,
                "contraindications": [],
                "video_url": "http://localhost:8002/storage/videos/deep_breathing.mp4"
            },
            {
                "name": "Rotación de cuello",
                "level": 1,
                "contraindications": ["dolor_articular"],
                "video_url": ""
            },
            {
                "name": "Básicos del Cuidado Articular",
                "level": 1,
                "contraindications": [],
                "video_url": "http://localhost:8002/storage/videos/articular_care.mp4"
            },
            {
                "name": "Estiramientos sentados en silla",
                "level": 1,
                "contraindications": [],
                "video_url": ""
            },
            {
                "name": "Recetas Saludables para el Corazón",
                "level": 1,
                "contraindications": [],
                "video_url": "http://localhost:8002/storage/videos/healthy_recipes.mp4"
            }
        ]
        
        for ex in default_exercises:
            # Evitar duplicados por nombre
            exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM exercises WHERE name = $1)", ex["name"]
            )
            if not exists:
                await conn.execute(
                    """INSERT INTO exercises (name, level, contraindications, video_url) 
                       VALUES ($1, $2, $3, $4)""",
                    ex["name"], ex["level"], ex["contraindications"], ex["video_url"]
                )
                print(f"Ejercicio sembrado: {ex['name']}")

        # 5. Sembrar usuarios por defecto (Senior y Cuidador)
        print("Sembrando usuarios de demostración...")
        # Clave hasheada: VitalPass123
        hashed_password = bcrypt.hash("VitalPass123")
        
        # Senior Demo User
        senior_email = "senior@vital.com"
        senior_profile = {
            "age": 75,
            "weight_kg": 68.5,
            "height_cm": 162.0,
            "fitness_level": "principiante",
            "goals": ["mejorar equilibrio", "aumentar flexibilidad"],
            "medical_restrictions": ["dolor_articular", "hipertensión"],
            "equipment": ["silla"],
            "preferred_schedule": "mañana"
        }
        
        senior_row = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1", senior_email
        )
        if not senior_row:
            senior_id = await conn.fetchval(
                """INSERT INTO users (email, role, profile, password) 
                   VALUES ($1, $2, $3, $4) RETURNING id""",
                senior_email, "senior", json.dumps(senior_profile), hashed_password
            )
            print(f"Usuario Senior sembrado: {senior_email} (ID: {senior_id})")
        else:
            senior_id = senior_row["id"]
            print(f"Usuario Senior ya existe: {senior_email}")

        # Caregiver Demo User
        caregiver_email = "caregiver@vital.com"
        caregiver_profile = {
            "name": "Laura Martínez",
            "relation": "Enfermera Residencia"
        }
        
        caregiver_row = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1", caregiver_email
        )
        if not caregiver_row:
            caregiver_id = await conn.fetchval(
                """INSERT INTO users (email, role, profile, password, linked_senior_id) 
                   VALUES ($1, $2, $3, $4, $5) RETURNING id""",
                caregiver_email, "caregiver", json.dumps(caregiver_profile), hashed_password, senior_id
            )
            print(f"Usuario Cuidador sembrado: {caregiver_email} (ID: {caregiver_id}, Vinculado a Senior)")
        else:
            caregiver_id = caregiver_row["id"]
            print(f"Usuario Cuidador ya existe: {caregiver_email}")
            # Asegurar vinculación por si acaso
            await conn.execute(
                "UPDATE users SET linked_senior_id = $1 WHERE id = $2", senior_id, caregiver_id
            )

        print("Inicialización y siembra completadas correctamente.")
    except Exception as e:
        print(f"Error durante la inicialización de las tablas o siembra: {e}")
        raise e
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(init_database())
