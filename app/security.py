import re
from typing import Optional
from pydantic import BaseModel, validator

class ClinicalSecurityGuard(BaseModel):
    response_text: str
    
    @validator('response_text')
    def check_clinical_safety(cls, v):
        # Expresiones regulares simples para detectar intenciones médicas
        diagnostic_patterns = [
            r"(?i)\b(tienes|usted tiene|podrías tener|sufres de)\b.*\b(cáncer|diabetes|hipertensión|infección|enfermedad)\b",
            r"(?i)\b(diagnóstico|diagnostico)\b",
        ]
        prescription_patterns = [
            r"(?i)\b(toma|tome|receto|prescribo)\b.*\b(mg|ml|pastillas|ibuprofeno|paracetamol|medicamento)\b",
            r"(?i)\b(debes tomar|deberías tomar)\b"
        ]
        emergency_patterns = [
            r"(?i)\b(dolor en el pecho|dificultad para respirar|sangrado profuso|pérdida de conocimiento)\b"
        ]
        
        needs_warning = False
        is_emergency = False
        
        for pattern in diagnostic_patterns + prescription_patterns:
            if re.search(pattern, v):
                needs_warning = True
                break
                
        for pattern in emergency_patterns:
            if re.search(pattern, v):
                is_emergency = True
                break
                
        warning_message = "\n\n**Aviso:** Soy un asistente de IA de bienestar, no un médico. Consulta a un profesional de la salud antes de modificar tu tratamiento."
        emergency_message = "\n\n**ALERTA MÉDICA:** Los síntomas que describes pueden requerir atención médica inmediata. Por favor, acude a urgencias o contacta a un profesional de la salud de inmediato."

        if is_emergency:
            # Reemplazar o añadir fuertemente
            return v + emergency_message
        if needs_warning:
            return v + warning_message
            
        return v
        
def apply_guardrails(text: str) -> str:
    guard = ClinicalSecurityGuard(response_text=text)
    return guard.response_text
