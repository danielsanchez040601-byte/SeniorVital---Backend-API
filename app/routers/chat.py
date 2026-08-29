from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage, SystemMessage

from ..schemas import ChatRequest, ChatResponse
from ..agents.wellness_coach import wellness_coach_agent, REACT_SYSTEM_PROMPT

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
    """Endpoint conversacional del Wellness Coach 2.0 con ReAct, Tool Calling y Guardrails clínicos."""
    try:
        react_result = await wellness_coach_agent.execute_react_cycle(
            user_id=str(req.user_id),
            query=req.query
        )
        raw_response_text = react_result.get("response", "")
        secured_response = apply_guardrails(raw_response_text)
        is_safe = secured_response == raw_response_text

        return ChatResponse(
            response=secured_response,
            is_safe=is_safe
        )

    except Exception as e:
        print(f"Error en chat_endpoint: {e}")
        return ChatResponse(
            response="Como su asistente de SeniorVital, le sugiero descansar, mantenerse hidratado y realizar estiramientos ligeros de bajo impacto.",
            is_safe=True
        )
