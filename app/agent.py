import os
from typing import Annotated, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from app.tools import (
    consultar_historial_medico, 
    registrar_evento_salud,
    analizar_fatiga_inactividad,
    ajustar_nivel_ejercicio,
    enviar_alerta_preventiva
)
# Estado del agente
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Leemos configuración desde las variables de entorno (.env)
openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
default_model = os.environ.get("DEFAULT_LLM_MODEL", "inclusionai/ling-3.0-flash:free")

if not openrouter_api_key:
    raise ValueError("OPENROUTER_API_KEY no está configurada en las variables de entorno (.env).")

# Herramientas unificadas para el agente de Wellness & Analytics
tools = [
    consultar_historial_medico, 
    registrar_evento_salud,
    analizar_fatiga_inactividad,
    ajustar_nivel_ejercicio,
    enviar_alerta_preventiva
]

# Instanciación del modelo LLM configurado para conectarse a OpenRouter
llm = ChatOpenAI(
    openai_api_key=openrouter_api_key,
    openai_api_base="https://openrouter.ai/api/v1",
    model_name=default_model,
    default_headers={
        "HTTP-Referer": "https://seniorvital.app",
        "X-Title": "Senior Vital AI"
    }
)

# LLM con herramientas para Function Calling
llm_with_tools = llm.bind_tools(tools)

async def agent_node(state: AgentState):
    """Nodo principal que invoca al LLM para decidir acciones o responder."""
    print("[Agent] Evaluando mensajes y razonando (Function Calling)...")
    # Al ser asíncrono, usamos ainvoke
    response = await llm_with_tools.ainvoke(state["messages"])
    return {"messages": [response]}

# Construir el grafo de LangGraph
builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools))

# Definir las transiciones
builder.add_edge(START, "agent")
# Si el agente decide usar una herramienta (devuelve tool_calls), va a "tools".
builder.add_conditional_edges(
    "agent",
    tools_condition,
)
# Después de ejecutar la herramienta, vuelve al agente para evaluar el resultado
builder.add_edge("tools", "agent")

# Agente autónomo compilado
wellness_agent = builder.compile()
