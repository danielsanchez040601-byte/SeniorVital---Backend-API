from pydantic import BaseModel, Field, validator
from typing import List, Optional


class HealthProfile(BaseModel):
    age: int = Field(ge=60, le=120)
    weight_kg: float = Field(ge=30, le=200)
    height_cm: float = Field(ge=100, le=250)
    fitness_level: str = Field(pattern="^(principiante|intermedio|avanzado)$")
    goals: List[str] = Field(min_length=1)
    medical_restrictions: List[str] = Field(default_factory=list)
    equipment: List[str] = Field(default_factory=list)
    preferred_schedule: Optional[str] = None

    @validator("medical_restrictions")
    def validate_restrictions(cls, v):
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
