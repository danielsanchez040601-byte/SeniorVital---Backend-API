"""Herramientas especializadas del NutritionAgent (SeniorVital 2.0).

Implementa herramientas clínicas para:
1. Cálculo de requerimientos nutricionales específicos para adultos mayores (+60).
2. Verificación de restricciones alimentarias ante patologías crónicas (diabetes, hipertensión).
"""

from __future__ import annotations

import logging
from typing import Any

from src.tools import Tool, ToolResult

logger = logging.getLogger(__name__)


class NutritionCalculatorTool(Tool):
    """Herramienta para calcular requerimientos nutricionales e hídricos geriátricos."""

    name = "nutrition_calculator"
    description = (
        "Calcula requerimientos energéticos basales, meta proteica diaria (1.0 - 1.2 g/kg) "
        "y volumen de hidratación recomendado para adultos mayores según edad, peso y nivel de actividad."
    )

    def validate_args(self, **kwargs) -> bool:
        weight = kwargs.get("weight_kg")
        if weight is None:
            return True  # Puede inferir con peso promedio
        try:
            return float(weight) > 20.0
        except (ValueError, TypeError):
            return False

    async def execute(self, **kwargs) -> ToolResult:
        try:
            weight = float(kwargs.get("weight_kg", 68.0))
            age = int(kwargs.get("age", 70))
            activity = str(kwargs.get("activity_level", "sedentario")).lower()

            # Cálculo calórico geriátrico adaptado (Harris-Benedict simplificado + factor gerontológico)
            base_kcal = 25.0 * weight if "activo" not in activity else 30.0 * weight
            # Factor proteico elevado para prevenir sarcopenia en adultos mayores: 1.0 - 1.2 g/kg
            protein_g = round(weight * 1.1, 1)
            # Hidratación geriátrica segura: 30 ml por kg de peso corporal
            hydration_ml = round(weight * 30.0)

            result_data = {
                "weight_kg": weight,
                "age": age,
                "estimated_calories_kcal": round(base_kcal),
                "protein_target_g": protein_g,
                "hydration_target_ml": hydration_ml,
                "recommendation_summary": (
                    f"Para un adulto mayor de {age} años ({weight} kg): meta calórica de ~{round(base_kcal)} kcal/día, "
                    f"al menos {protein_g}g de proteína de alto valor biológico para prevención de sarcopenia, "
                    f"y una ingesta hídrica mínima de {hydration_ml} ml (~{round(hydration_ml/250, 1)} vasos de agua)."
                ),
            }
            return ToolResult(success=True, data=result_data, tool_name=self.name)
        except Exception as e:
            logger.error(f"Error en {self.name}: {e}")
            return ToolResult(success=False, error=str(e), tool_name=self.name)


class ClinicalDietaryCheckTool(Tool):
    """Herramienta de verificación dietética contra condiciones clínicas geriátricas."""

    name = "clinical_dietary_check"
    description = (
        "Evalúa si un alimento, comida o receta es segura para un adulto mayor con condiciones crónicas "
        "como hipertensión arterial (control de sodio), diabetes mellitus tipo 2 (índice glucémico) o insuficiencia cardíaca."
    )

    def validate_args(self, **kwargs) -> bool:
        food = kwargs.get("food") or kwargs.get("query")
        return bool(food and isinstance(food, str))

    async def execute(self, **kwargs) -> ToolResult:
        try:
            food = str(kwargs.get("food") or kwargs.get("query", "")).lower()
            conditions = kwargs.get("conditions") or []
            if isinstance(conditions, str):
                conditions = [c.strip().lower() for c in conditions.split(",")]
            else:
                conditions = [str(c).lower() for c in conditions]

            warnings = []
            safe = True
            alternatives = []

            # Reglas clínicas deterministas para adultos mayores
            is_hypertensive = any("hipertens" in c or "presi" in c for c in conditions)
            is_diabetic = any("diabet" in c or "gluc" in c for c in conditions)
            has_osteoporosis = any("osteo" in c for c in conditions)

            # Verificación de Sodio / Hipertensión
            high_sodium = ["pizza", "embutido", "salchicha", "jamon", "snack", "enlatado", "soja", "frito"]
            if is_hypertensive and any(item in food for item in high_sodium):
                safe = False
                warnings.append("Alto contenido de sodio: riesgo de elevación de presión arterial sistólica.")
                alternatives.append("Preparaciones caseras con hierbas aromáticas sin sal añadida.")

            # Verificación de Azúcar / Diabetes
            high_glycemic = ["dulce", "azucar", "pastel", "gaseosa", "refresco", "miel", "helado", "pan blanco"]
            if is_diabetic and any(item in food for item in high_glycemic):
                safe = False
                warnings.append("Elevado índice glucémico: riesgo de hiperglucemia reactiva.")
                alternatives.append("Carbohidratos complejos ricos en fibra (avena integral, legumbres) y frutas de bajo índice glucémico.")

            # Recomendación para salud ósea
            if has_osteoporosis:
                alternatives.append("Asegurar aporte de calcio y vitamina D (lácteos descremados, pescados pequeños con espinas, hojas verdes).")

            result_data = {
                "food_evaluated": food,
                "conditions_considered": conditions,
                "is_safe": safe,
                "clinical_warnings": warnings,
                "suggested_alternatives": alternatives,
                "clinical_note": (
                    "Aprobado con precauciones habituales."
                    if safe
                    else "Alimento con contraindicaciones moderadas o altas para las patologías declaradas."
                ),
            }
            return ToolResult(success=True, data=result_data, tool_name=self.name)
        except Exception as e:
            logger.error(f"Error en {self.name}: {e}")
            return ToolResult(success=False, error=str(e), tool_name=self.name)
