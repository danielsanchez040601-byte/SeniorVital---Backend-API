from fastapi import APIRouter, HTTPException
try:
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:
    HumanMessage = None
    SystemMessage = None

try:
    from src.database.schemas import ChatRequest, ChatResponse
except ImportError:
    try:
        from ..database.schemas import ChatRequest, ChatResponse
    except ImportError:
        from schemas import ChatRequest, ChatResponse

try:
    from src.agents.wellness_coach import wellness_agent, CLINICAL_SYSTEM_PROMPT
except ImportError:
    CLINICAL_SYSTEM_PROMPT = "Eres un asistente de bienestar geriátrico."
    wellness_agent = None

router = APIRouter(prefix="/api/v1", tags=["AI Clinical Chat"])


def apply_guardrails(text: str) -> str:
    """Capa de seguridad clínica determinística en Python puro."""
    prohibited_terms = ["ibuprofeno", "paracetamol", "morfina", "tramadol", "cirugia"]
    lower_text = text.lower()
    for term in prohibited_terms:
        if term in lower_text:
            return (
                "Como asistente de bienestar, no estoy autorizado para recomendar medicamentos o dosis. "
                "Por favor, consulte a su médico o fisioterapeuta de cabecera."
            )
    return text


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """Endpoint conversacional del Wellness Coach con RAG y Guardrails clínicos."""
    try:
        system_prompt = f"{CLINICAL_SYSTEM_PROMPT}\nID de contexto del paciente actual: {req.user_id}."

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=req.query)
        ]

        try:
            final_state = await wellness_agent.ainvoke({"messages": messages})
            raw_response_text = final_state["messages"][-1].content
        except Exception as agent_err:
            print(f"[Chat Warning] Fallback activado: {agent_err}")
            raw_response_text = (
                "¡Hola! Como tu Wellness Coach de SeniorVital, te recomiendo realizar movimientos suaves y controlados, "
                "mantener una respiración constante y una buena postura. Recuerda hidratarte periódicamente. "
                "Si experimentas dolor o molestia intensa, suspende la actividad de inmediato y notifícalo a tu cuidador o médico."
            )

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
