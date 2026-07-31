from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(req: LoginRequest = None):
    # Endpoint mock de login
    return {
        "access_token": "token-simulado-seniorvital",
        "token_type": "bearer"
    }

@router.get("/me")
async def get_me():
    # Endpoint mock para devolver el perfil básico
    return {
        "id": 1,
        "name": "Usuario Demo",
        "role": "paciente"
    }
