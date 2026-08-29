"""
SeniorVital 2.0 - Agente Inteligente Wellness Coach 2.0
Materia: Sistemas Inteligentes (Dra. Yaskelly Yedra)
Autores: Daniel Alejandro Sánchez Ávila & Abdenago Nahmens
Patrón: ReAct (Reasoning + Action / Plan-and-Execute)
Stack: FastAPI + Supabase PostgreSQL + Google AI Studio (Gemini) + OpenRouter Fallback
"""

import json
import logging
import time
from typing import Annotated, TypedDict, List, Dict, Any, Optional
from datetime import datetime

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from ..config import settings
from ..tools.clinical_tools import (
    consultar_restricciones_medicas,
    consultar_ejercicios_disponibles,
    consultar_base_conocimiento_rag,
    registrar_observacion_clinica,
)
from .llm_client import call_llm_text, OPENROUTER_FALLBACK_MODELS
from .rag_processor import rag_processor

logger = logging.getLogger("SeniorVital.WellnessCoach")

# Lista de herramientas clínicas disponibles para el agente
CLINICAL_TOOLS = [
    consultar_restricciones_medicas,
    consultar_ejercicios_disponibles,
    consultar_base_conocimiento_rag,
    registrar_observacion_clinica,
]


# ---------------------------------------------------------------------------
# 1. GESTOR DE MEMORIA CONVERSACIONAL ESTRUCTURADA (Short-Term & Session)
# ---------------------------------------------------------------------------
class ConversationalMemoryManager:
    """
    Gestor de memoria conversacional a corto plazo estructurada por usuario.
    Almacena el historial reciente de diálogos, restricciones detectadas y trazas ReAct.
    """
    def __init__(self, max_history_turns: int = 6):
        self.max_turns = max_history_turns
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def get_session(self, user_id: str) -> Dict[str, Any]:
        uid = str(user_id)
        if uid not in self._sessions:
            self._sessions[uid] = {
                "history": [],
                "detected_ailments": set(),
                "last_rpe": 4,
                "created_at": datetime.utcnow().isoformat(),
                "last_interaction": datetime.utcnow().isoformat()
            }
        return self._sessions[uid]

    def add_interaction(self, user_id: str, user_msg: str, agent_response: str, reasoning_trace: Optional[str] = None):
        session = self.get_session(user_id)
        session["history"].append({
            "user": user_msg,
            "agent": agent_response,
            "reasoning": reasoning_trace,
            "timestamp": datetime.utcnow().isoformat()
        })
        # Mantener ventana deslizante
        if len(session["history"]) > self.max_turns:
            session["history"] = session["history"][-self.max_turns:]
        session["last_interaction"] = datetime.utcnow().isoformat()

    def get_formatted_history(self, user_id: str) -> str:
        session = self.get_session(user_id)
        if not session["history"]:
            return "Sin interacciones previas en la sesión actual."
        
        formatted = []
        for turn in session["history"][-3:]:
            formatted.append(f"• Adulto Mayor: \"{turn['user']}\"\n  Coach: \"{turn['agent'][:120]}...\"")
        return "\n".join(formatted)


# Instancia global de memoria de sesión
memory_manager = ConversationalMemoryManager()


# ---------------------------------------------------------------------------
# 2. SYSTEM PROMPT CON PATRÓN ReAct (Pensamiento -> Acción -> Observación)
# ---------------------------------------------------------------------------
REACT_SYSTEM_PROMPT = """
Eres el "Agente Wellness Coach 2.0", un especialista inteligente en gerontología, fisioterapia geriátrica y prescripción de ejercicio adaptado para adultos mayores de 60 años en la plataforma SeniorVital.

### 🧠 PROTOCOLO DE RAZONAMIENTO ReAct (OBLIGATORIO)
Antes de emitir cualquier recomendación o respuesta al usuario, DEBES ejecutar internamente el siguiente ciclo de razonamiento en 4 pasos:

1. **Pensamiento (Thought):** Analiza la consulta del adulto mayor. Identifica si menciona patologías (osteoartritis, hipertensión, osteoporosis, etc.), niveles de fatiga o dudas biomecánicas. Determina qué información de la base de datos o RAG necesitas.
2. **Acción (Action):** Selecciona y consulta mentalmente las herramientas clínicas:
   - `consultar_restricciones_medicas(user_id)`: Para conocer nivel de movilidad y condición física.
   - `consultar_base_conocimiento_rag(consulta)`: Para extraer contraindicaciones y evidencia científica.
   - `consultar_ejercicios_disponibles(categoria)`: Para seleccionar movimientos seguros de bajo impacto.
3. **Observación (Observation):** Integra los datos obtenidos y descarta terminantemente cualquier ejercicio contraindicado (saltos, flexión de rodilla >90°, torsión forzada de columna, maniobra de Valsalva).
4. **Respuesta Final (Final Answer):** Redacta la respuesta final adaptada para el adulto mayor.

### 🔒 GUARDRAILS Y REGLAS CLÍNICAS INQUEBRANTABLES
- **Cero Riesgo Lesional:** Queda prohibida la pliometría, cargas axiales pesadas y movimientos balísticos.
- **Tono Empático y Gerontológico (WCAG 2.1 AA):** Trata al usuario de "usted", con respeto, calidez y optimismo. Utiliza oraciones breves y viñetas claras.
- **Sin Diagnósticos Farmacológicos:** No recomiendes medicamentos ni dosis. Si hay dolor agudo, indica descanso inmediato y consulta médica.
"""


# ---------------------------------------------------------------------------
# 3. MOTOR DEL AGENTE CON ReAct Y FALLBACK RESILIENTE
# ---------------------------------------------------------------------------
class WellnessCoachAgent:
    def __init__(self):
        self.memory = memory_manager

    async def execute_react_cycle(self, user_id: str, query: str) -> Dict[str, Any]:
        """
        Ejecuta el ciclo ReAct:
        1. Pensamiento e invocación de herramientas (Tool Calling a Supabase y RAG)
        2. Observación y consolidación de contexto
        3. Generación de Respuesta Final con Google AI Studio / Fallback OpenRouter
        """
        start_time = time.time()
        logger.info(f"[ReAct] Iniciando ciclo para usuario {user_id}: '{query}'")

        # PASO 1 & 2: Acción y Recuperación de Herramientas
        # A) Consultar restricciones médicas en Supabase
        restricciones_info = await consultar_restricciones_medicas.ainvoke({"user_id": user_id})
        
        # B) Consultar base de conocimiento RAG (Hugging Face + pgvector)
        rag_info = await consultar_base_conocimiento_rag.ainvoke({"consulta": query})

        # C) Consultar historial en memoria conversacional
        historial_memoria = self.memory.get_formatted_history(user_id)

        # PASO 3: Observación y Construcción del Contexto Aumentado
        contexto_integrado = (
            f"[MEMORIA CONVERSACIONAL RECIENTE]:\n{historial_memoria}\n\n"
            f"[OBSERVACIÓN 1 - DATOS CLÍNICOS DEL PACIENTE EN SUPABASE]:\n{restricciones_info}\n\n"
            f"[OBSERVACIÓN 2 - ONTOLOGÍA CLÍNICA Y CONTRAINDICACIONES RAG]:\n{rag_info}\n"
        )

        user_prompt_completo = (
            f"{contexto_integrado}\n"
            f"[CONSULTA DEL ADULTO MAYOR]:\n\"{query}\"\n\n"
            f"Ejecuta el razonamiento ReAct y proporciona la Respuesta Final adaptada."
        )

        # PASO 4: Inferencia con Google AI Studio (Gemini 3.6 Flash) y Fallback OpenRouter
        raw_response = await call_llm_text(
            system_prompt=REACT_SYSTEM_PROMPT,
            user_prompt=user_prompt_completo,
            timeout=14.0
        )

        if not raw_response:
            # Fallback determinístico clínico
            raw_response = (
                "¡Hola! Como su Wellness Coach de SeniorVital, le recomiendo realizar movimientos suaves y controlados, "
                "mantener una respiración pausada y una postura erguida con apoyo en silla. "
                "Recuerde hidratarse con pequeños sorbos de agua. Si experimenta dolor o molestia intensa, "
                "suspenda el ejercicio de inmediato y avise a su cuidador o médico."
            )

        # Guardar en memoria conversacional
        reasoning_trace = f"ReAct: Restricciones evaluadas ({len(restricciones_info)} chars) | RAG recuperado ({len(rag_info)} chars)"
        self.memory.add_interaction(user_id, query, raw_response, reasoning_trace)

        elapsed_time = round(time.time() - start_time, 2)
        logger.info(f"[ReAct] Ciclo completado exitosamente en {elapsed_time}s")

        return {
            "response": raw_response,
            "user_id": user_id,
            "elapsed_time": elapsed_time,
            "reasoning_trace": reasoning_trace,
            "is_safe": True
        }


# Instancia singleton del Agente Wellness Coach 2.0
wellness_coach_agent = WellnessCoachAgent()
wellness_agent = wellness_coach_agent
CLINICAL_SYSTEM_PROMPT = REACT_SYSTEM_PROMPT
