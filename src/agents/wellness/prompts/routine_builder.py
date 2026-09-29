"""Routine prompt builder — construye prompts para generación de rutinas.

Extraído de routines-ai-service/main.py build_prompt().
"""

import json


class RoutinePromptBuilder:
    """Construye prompts para generación de rutinas de ejercicio.

    Precondiciones: None.
    Postcondiciones: Retorna string formateado para el LLM.
    Efectos secundarios: None (función pura).
    """

    SYSTEM_PROMPT = (
        "Eres un entrenador personal especializado en adultos mayores. "
        "Genera rutinas de ejercicio seguras, efectivas y adaptadas al perfil del usuario. "
        "Responde SIEMPRE en español latinoamericano. "
        "Prioriza la seguridad del usuario sobre la intensidad del ejercicio."
    )

    def build_system_prompt(self) -> str:
        """Retorna el prompt de sistema base."""
        return self.SYSTEM_PROMPT

    def build(
        self,
        profile: dict,
        health_profile: dict,
        preferences: dict,
        safe_exercises: list,
    ) -> str:
        """Construye el prompt completo con perfil del usuario y ejercicios.

        Args:
            profile: Perfil adicional del usuario (jsonb).
            health_profile: Perfil de salud (edad, peso, restricciones).
            preferences: Preferencias del usuario (favoritos, evitar).
            safe_exercises: Lista de ejercicios sin contraindicaciones.

        Returns:
            Prompt formateado para el modelo LLM.
        """
        age = health_profile.get("age", profile.get("age", "desconocida"))
        fitness_level = health_profile.get(
            "fitness_level", profile.get("fitness_level", "bajo")
        )
        goals = health_profile.get("goals", profile.get("goals", []))
        medical_restrictions = health_profile.get(
            "medical_restrictions", profile.get("medical_restrictions", [])
        )
        equipment = health_profile.get("equipment", profile.get("equipment", []))
        conditions = health_profile.get("conditions", [])
        medications = health_profile.get("medications", [])
        wake_time = health_profile.get("wake_time", "08:00")
        sleep_time = health_profile.get("sleep_time", "22:00")
        duration_pref = health_profile.get("duration_pref", 30)

        favorite_exercises = preferences.get("favorite_exercises", [])
        avoid_exercises = preferences.get("avoid_exercises", [])

        exercise_list = []
        for ex in safe_exercises:
            exercise_list.append({
                "id": ex.get("id", 0),
                "name": ex.get("name", ""),
                "description": ex.get("description", ""),
                "level": ex.get("level", 1),
                "duration_min": ex.get("duration_min", 5),
                "contraindications": (
                    ex.get("contraindications", "").split(",")
                    if ex.get("contraindications")
                    else []
                ),
            })

        return f"""
Genera una rutina de ejercicios para un adulto mayor con el siguiente perfil DETALLADO:

PERFIL DEL USUARIO:
- Edad: {age}
- Nivel de condición física: {fitness_level}
- Objetivos: {', '.join(goals) if goals else 'mantener actividad'}
- Equipo disponible: {', '.join(equipment) if equipment else 'ninguno'}
- Condiciones médicas: {', '.join(conditions) if conditions else 'ninguna'}
- Medicamentos: {', '.join(medications) if medications else 'ninguno'}
- Restricciones médicas/contraindicaciones: {', '.join(medical_restrictions) if medical_restrictions else 'ninguna'}
- Horario: se levanta a las {wake_time}, duerme a las {sleep_time}
- Duración preferida: {duration_pref} minutos

PREFERENCIAS:
- Ejercicios favoritos: {', '.join(favorite_exercises) if favorite_exercises else 'ninguno'}
- Ejercicios a evitar: {', '.join(avoid_exercises) if avoid_exercises else 'ninguno'}

EJERCICIOS DISPONIBLES SEGUROS (usa los IDs para referenciar):
{json.dumps(exercise_list, ensure_ascii=False)}

INSTRUCCIONES:
1. Prioriza ejercicios favoritos si son seguros.
2. Evita ejercicios en "evitar" y cualquier ejercicio con contraindicaciones que coincidan con restricciones.
3. Incluye un ejercicio de calentamiento suave (2-3 min).
4. Cada ejercicio debe tener: exercise_id (número del catálogo), name, sets, reps, duration_min, rest_duration_sec.
5. Total de ejercicios: 3-4. Duración total: ~{duration_pref} minutos.

Responde SOLO con JSON válido:
{{
  "exercises": [
    {{"exercise_id": 1, "name": "string", "sets": 2, "reps": 8, "duration_min": 5, "rest_duration_sec": 30, "description": "string"}}
  ],
  "warmup": [
    {{"name": "string", "sets": 1, "reps": 5, "duration_min": 2, "description": "string"}}
  ]
}}
"""
