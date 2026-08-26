"""Modelos de dominio compartidos con validación Pydantic.

Define el perfil de salud de un adulto mayor con sus restricciones
médicas, nivel de condición física y preferencias.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class HealthProfile(BaseModel):
    """Perfil de salud y condición física de un adulto mayor.

    Validado contra rangos y valores permitidos antes de persistir
    como JSONB en la tabla users.
    """

    age: int = Field(ge=60, le=120)
    weight_kg: float = Field(ge=30, le=200)
    height_cm: float = Field(ge=100, le=250)
    fitness_level: str = Field(pattern="^(principiante|intermedio|avanzado)$")
    goals: List[str] = Field(min_length=1)
    medical_restrictions: List[str] = Field(default_factory=list)
    equipment: List[str] = Field(default_factory=list)
    preferred_schedule: Optional[str] = None

    @field_validator("medical_restrictions")
    @classmethod
    def validate_restrictions(cls, v):
        """Valida que cada restricción médica esté en el conjunto permitido."""
        allowed = {
            "artrosis_rodilla",
            "osteoporosis",
            "hipertensión",
            "dolor_articular",
            "prótesis",
        }
        for item in v:
            if item not in allowed:
                raise ValueError(f"Restricción no permitida: {item}")
        return v
