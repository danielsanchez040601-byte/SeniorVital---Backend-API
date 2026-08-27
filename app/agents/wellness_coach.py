import os
from typing import Annotated, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from ..config import settings
from ..tools.vector_tools import consultar_historial_medico, registrar_evento_salud
from .llm_client import call_llm_text, OPENROUTER_FALLBACK_MODELS


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# Herramientas clínicas asignadas al Wellness Coach
tools = [consultar_historial_medico, registrar_evento_salud]


CLINICAL_SYSTEM_PROMPT = """
Eres el "Agente Wellness Coach", un asistente médico preventivo y experto en gerontología de la plataforma inteligente "Senior Vital". Tu objetivo principal es ayudar a adultos mayores (+60 años) a mejorar de forma segura su movilidad, flexibilidad, resistencia y fuerza en casa.

### 🔒 REGLAS Y GUARDRAILS CLÍNICOS (OBLIGATORIO)
1. **Filtro Proactivo de Patologías:** Antes de emitir o sugerir cualquier rutina, DEBES consultar obligatoriamente el perfil clínico del usuario (restricciones médicas como hipertensión, artritis, osteoporosis, prótesis, etc.) almacenado en la base de datos.
2. **Cero Riesgo de Lesión:** Tienes estrictamente prohibido prescribir ejercicios de alto impacto, saltos, flexiones forzadas de columna o cargas axiales pesadas si el usuario presenta contraindicaciones en su historial. Limita las rutinas estrictamente a un máximo de 3 a 4 niveles de progresión segura (ej. sentados, asistidos o de bajo impacto).
3. **Uso de Herramientas (Tool Calling):** Cuando el usuario mencione un nuevo síntoma, medicamento, horario o cambio en su salud, DEBES invocar la herramienta correspondiente para registrar o actualizar su memoria semántica (RAG) en la base de datos antes de responder.

### 💬 TONO Y COMUNICACIÓN (Accesibilidad Gerontológica)
- **Empático y Positivo:** Utiliza un lenguaje cálido, claro y motivador tratando al usuario de "usted". Está terminantemente prohibido usar un tono culpabilizador, alarmista o mencionar "rachas punitivas" si el usuario deja de entrenar ("cada pequeño paso cuenta").
- **Claridad Visual:** Redacta respuestas directas, sin rodeos técnicos complejos, estructuradas en pasos sencillos o viñetas fáciles de leer.

### 🛠️ CAPACIDADES TÉCNICAS
- Procesas consultas en lenguaje natural integrando el contexto recuperado de la base de datos vectorial (Supabase / pgvector).
- Evalúas la Escala de Esfuerzo Percibido (RPE) reportada por el usuario para sugerir ajustes dinámicos en las cargas de las sesiones futuras.
"""


async def agent_node(state: AgentState):
    """Nodo del agente que invoca el LLM con razonamiento clínico y Fallback Resiliente."""
    messages = state["messages"]
    last_msg = messages[-1].content if messages else "¿Cómo puedo ejercitarme seguro hoy?"

    # 1. Intento primario y fallback multimodelo mediante el cliente central
    ai_response = await call_llm_text(
        system_prompt=CLINICAL_SYSTEM_PROMPT,
        user_prompt=str(last_msg),
        timeout=12.0
    )

    if ai_response:
        return {"messages": [AIMessage(content=ai_response)]}

    # 2. Respaldo secundario: LangChain ChatOpenAI con enlace a Tools
    if settings.OPENROUTER_API_KEY:
        for model_name in OPENROUTER_FALLBACK_MODELS:
            try:
                llm = ChatOpenAI(
                    openai_api_key=settings.OPENROUTER_API_KEY,
                    openai_api_base="https://openrouter.ai/api/v1",
                    model_name=model_name,
                    timeout=10.0,
                    default_headers={
                        "HTTP-Referer": "https://seniorvital-backend.onrender.com",
                        "X-Title": "Senior Vital Wellness Coach"
                    }
                )
                llm_with_tools = llm.bind_tools(tools)
                response = await llm_with_tools.ainvoke(messages)
                return {"messages": [response]}
            except Exception as e:
                print(f"⚠️ [WellnessCoach OpenRouter Tool Error] {model_name}: {e}")

    # 3. Mecanismo de degradación clínica elegante
    print("🛡️ [WellnessCoach] Activando respuesta clínica segura por degradación elegante.")
    fallback_text = (
        "¡Hola! Como tu Wellness Coach de SeniorVital, te recomiendo realizar movimientos suaves y controlados, "
        "mantener una respiración constante y una buena postura. Recuerda hidratarte periódicamente. "
        "Si experimentas dolor articular o molestia, detén la actividad y consulta a tu fisioterapeuta."
    )
    return {"messages": [AIMessage(content=fallback_text)]}


# Construir el grafo de LangGraph
builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")

wellness_agent = builder.compile()
