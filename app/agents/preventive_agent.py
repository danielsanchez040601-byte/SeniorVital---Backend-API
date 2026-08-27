from datetime import datetime, timedelta
from typing import Dict, Any


def evaluar_riesgo_paciente(historial_rpe: list, dias_inactividad: int, dolor_reportado: bool = False) -> Dict[str, Any]:
    """
    Evalúa el semáforo de riesgo clínico de un adulto mayor:
    - VERDE: Activo, RPE promedio <= 6, sin dolor severo.
    - ÁMBAR: Inactividad 3-5 días o RPE promedio 7-8.
    - ROJO: Inactividad > 5 días, RPE 9-10 reiterado o dolor articular agudo.
    """
    if not historial_rpe:
        rpe_promedio = 0
    else:
        rpe_promedio = sum(historial_rpe) / len(historial_rpe)

    # Regla 1: Riesgo Alto (Rojo)
    if dias_inactividad > 5 or rpe_promedio >= 8.5 or dolor_reportado:
        return {
            "nivel": "ROJO",
            "color": "#881337",
            "accion_recomendada": "Ajuste manual prioritario por Fisioterapeuta y reducción inmediata de intensidad.",
            "rpe_promedio": round(rpe_promedio, 1),
            "dias_inactividad": dias_inactividad,
            "requiere_intervencion": True
        }

    # Regla 2: Riesgo Medio (Ámbar)
    if dias_inactividad >= 3 or rpe_promedio >= 7.0:
        return {
            "nivel": "AMBAR",
            "color": "#D97706",
            "accion_recomendada": "Enviar notificación de ánimo preventiva y monitorear fatiga en la próxima sesión.",
            "rpe_promedio": round(rpe_promedio, 1),
            "dias_inactividad": dias_inactividad,
            "requiere_intervencion": False
        }

    # Regla 3: Buen Estado (Verde)
    return {
        "nivel": "VERDE",
        "color": "#4A6B5B",
        "accion_recomendada": "Mantener progresión actual y felicitar adherencia constante.",
        "rpe_promedio": round(rpe_promedio, 1),
        "dias_inactividad": dias_inactividad,
        "requiere_intervencion": False
    }


def procesar_alerta_fatiga(senior_id: int, rpe: int, dolor: str = None) -> Dict[str, Any]:
    """Genera evento de alerta si el esfuerzo supera los umbrales seguros."""
    es_alta_fatiga = rpe >= 8
    tiene_dolor = bool(dolor and dolor.lower() not in ["sin dolor", "ninguno", "ninguna", "no"])

    return {
        "senior_id": senior_id,
        "es_alerta": es_alta_fatiga or tiene_dolor,
        "mensaje": f"Alerta de esfuerzo RPE {rpe}/10 reportada." if es_alta_fatiga else "Sesión dentro de parámetros normales.",
        "dolor_zona": dolor if tiene_dolor else None,
        "ajuste_sugerido": "Reducir series en 50% para próxima sesión" if es_alta_fatiga else "Continuar plan"
    }


async def evaluar_riesgo_fatiga(paciente_id: str, rpe_score: int, dolor_reportado: str = None, db=None) -> Dict[str, Any]:
    """Evalúa la fatiga clínica, el esfuerzo RPE reportado y el riesgo de abandono."""
    es_alta_fatiga = rpe_score >= 8
    tiene_dolor = bool(dolor_reportado and dolor_reportado.lower() not in ["sin dolor", "ninguno", "ninguna", "no"])

    nivel = "BAJO"
    if es_alta_fatiga or tiene_dolor:
        nivel = "ALTO" if (rpe_score >= 9 or tiene_dolor) else "MEDIO"

    return {
        "paciente_id": str(paciente_id),
        "user_id": str(paciente_id),
        "rpe_score": rpe_score,
        "riesgo": nivel.lower(),
        "nivel_riesgo": nivel,
        "es_alerta": es_alta_fatiga or tiene_dolor,
        "dolor_reportado": dolor_reportado,
        "status": "evaluado",
        "accion_recomendada": (
            "Intercalar ejercicios en silla y reducir repeticiones en la próxima sesión."
            if es_alta_fatiga or tiene_dolor
            else "Mantener progresión actual y felicitar adherencia constante."
        )
    }

