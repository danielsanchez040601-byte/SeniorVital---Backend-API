import os
from dotenv import load_dotenv

# Cargar variables de entorno antes de importar
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.agent import wellness_agent
from app.security import apply_guardrails
from app.database import engine, Base
from app.routers import users, exercises, auth, routines
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Senior Vital Autonomous AI Service", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(users.router)
app.include_router(exercises.router)
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(routines.router)

class ChatRequest(BaseModel):
    user_id: str
    query: str

class ChatResponse(BaseModel):
    response: str
    is_safe: bool

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    try:
        # 1. CONTEXTO BASE DEL AGENTE
        # El agente ahora es 100% autónomo y decidirá si debe usar la herramienta para
        # buscar historial médico o registrar eventos.
        system_prompt = (
            "Eres el Wellness Coach de Senior Vital. Sé empático y ayuda a los usuarios "
            "con sus rutinas y dudas de bienestar. "
            "IMPORTANTE: Tienes acceso a herramientas para interactuar con la Memoria Semántica. "
            f"El ID del paciente con el que hablas es: {req.user_id}. "
            "Úsalo SIEMPRE que llames a consultar_historial_medico o registrar_evento_salud. "
            "Si el paciente te cuenta un síntoma nuevo o algo relevante, regístralo proactivamente."
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=req.query)
        ]

        # 2. INVOCACIÓN DEL AGENTE AUTÓNOMO (LangGraph) CON FALLBACK RESILIENTE
        try:
            final_state = await wellness_agent.ainvoke({"messages": messages})
            agent_response_msg = final_state["messages"][-1]
            raw_response_text = agent_response_msg.content
        except Exception as agent_err:
            print(f"[Agent Warning] Conmutando a fallback clínico: {agent_err}")
            raw_response_text = (
                "¡Hola! Como tu Wellness Coach de SeniorVital, te recomiendo realizar movimientos suaves y controlados, "
                "mantener una respiración constante y una buena postura. Recuerda hidratarte periódicamente. "
                "Si experimentas dolor o molestia intensa, suspende la actividad de inmediato y notifícalo a tu cuidador o médico."
            )

        # 3. CAPA DE SEGURIDAD CLÍNICA (Guardrails determinísticos en Python puro)
        secured_response = apply_guardrails(raw_response_text)
        is_safe = secured_response == raw_response_text

        return ChatResponse(
            response=secured_response,
            is_safe=is_safe
        )

    except Exception as e:
        print(f"Error en chat_endpoint: {e}")
        return ChatResponse(
            response="Como tu asistente de SeniorVital, te sugiero descansar, mantenerte hidratado y realizar estiramientos ligeros de bajo impacto.",
            is_safe=True
        )
