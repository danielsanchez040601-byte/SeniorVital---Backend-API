import os
from typing import Annotated, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
import httpx
import json

from ..config import settings
from ..tools.vector_tools import consultar_historial_medico, registrar_evento_salud


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# Herramientas clínicas asignadas al Wellness Coach
tools = [consultar_historial_medico, registrar_evento_salud]

# Configuración del LLM
gemini_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY
openrouter_key = settings.OPENROUTER_API_KEY
default_model = settings.DEFAULT_LLM_MODEL
if default_model == "google/gemma-4-31b:free":
    default_model = "google/gemma-4-31b-it:free"

llm = ChatOpenAI(
    openai_api_key=openrouter_key or "sk-dummy-key",
    openai_api_base="https://openrouter.ai/api/v1",
    model_name=default_model,
    default_headers={
        "HTTP-Referer": "https://seniorvital-backend.onrender.com",
        "X-Title": "Senior Vital Wellness Coach"
    }
)
llm_with_tools = llm.bind_tools(tools)


async def agent_node(state: AgentState):
    """Nodo del agente que invoca el LLM con razonamiento clínico."""
    messages = state["messages"]

    # 1. Prioridad: Google AI Studio Directo si está configurado
    if gemini_key:
        try:
            last_msg = messages[-1].content
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={gemini_key}"
            payload = {
                "contents": [{"parts": [{"text": f"Eres el Wellness Coach gerontológico de SeniorVital. Sé empático, cálido y conciso. Responde la siguiente consulta de salud/ejercicio:\n{last_msg}"}]}]
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                    from langchain_core.messages import AIMessage
                    return {"messages": [AIMessage(content=text.strip())]}
        except Exception as e:
            print(f"[WellnessCoach Google Fallback] {e}")

    # 2. Respaldo: OpenRouter con function calling
    try:
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}
    except Exception as e:
        print(f"[WellnessCoach OpenRouter Fallback] {e}")
        from langchain_core.messages import AIMessage
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
