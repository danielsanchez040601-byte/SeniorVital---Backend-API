"""Wellness Coach Prompt Builder — prompts para el agente conversacional."""

import json
from typing import Any

from src.memory import Message


SYSTEM_PROMPT_BASE = """Eres el Wellness Coach de SeniorVital, un coach de bienestar para adultos mayores en Latinoamérica.

## REGLAS
1. SEGURIDAD: Si hay duda sobre salud, recomienda consultar a un profesional.
2. EMPATÍA: Habla como un amigo que se preocupa. Tono cálido y motivacional.
3. IDIOMA: Responde SIEMPRE en español.
4. FORMATO: Responde SOLO con JSON válido, sin texto adicional.
5. LÍMITES: No des diagnósticos médicos.

## FORMATO DE RESPUESTA
Para responder al usuario, usa EXCLUSIVAMENTE este JSON:
{"thought": "tu razonamiento", "final_answer": "tu respuesta al usuario"}

Si necesitas una herramienta, usa:
{"thought": "tu razonamiento", "action": "nombre_tool", "action_input": {"param": "valor"}}
"""

REACT_FORMAT_INSTRUCTIONS = """

## HERRAMIENTAS DISPONIBLES
{tools_desc}

## EJEMPLO
Usuario: ¿Qué ejercicios puedo hacer?
Respuesta: {{"thought": "El usuario quiere ejercicios. Voy a buscar en el catálogo.", "action": "exercise_catalog", "action_input": {{"category": "general"}}}}

Usuario: ¿Cómo estás?
Respuesta: {{"thought": "Saludo simple, respondo directamente.", "final_answer": "¡Hola! Estoy bien, gracias por preguntar. ¿Cómo puedo ayudarte hoy?"}}
"""


class WellnessCoachPromptBuilder:
    """Construye prompts para el Wellness Coach Agent 2.0.

    Precondiciones: None.
    Postcondiciones: Retorna (system_prompt, user_prompt) tuple.
    Efectos secundarios: None (función pura).
    """

    def build(
        self,
        user_message: str,
        user_profile: dict[str, Any],
        conversation_history: list[Message],
        tool_results: list | None = None,
        available_tools: list | None = None,
    ) -> tuple[str, str]:
        """Construye (system_prompt, user_prompt) para el LLM.

        Args:
            user_message: Mensaje actual del usuario.
            user_profile: Perfil del usuario (salud, preferencias).
            conversation_history: Historial de la conversación.
            tool_results: Resultados de herramientas ejecutadas.
            available_tools: Herramientas disponibles para el agente.

        Returns:
            Tupla (system_prompt, user_prompt).
        """
        system = self._build_system_prompt(available_tools or [])
        user = self._build_user_prompt(
            user_message, user_profile, conversation_history, tool_results or []
        )
        return system, user

    def _build_system_prompt(self, tools: list) -> str:
        """Incluye descripción de herramientas y formato ReAct."""
        if tools:
            tools_desc = "\n".join(
                f"- {t.name}: {t.description}" for t in tools
            )
        else:
            tools_desc = "No hay herramientas disponibles."

        return f"{SYSTEM_PROMPT_BASE}\n\n{REACT_FORMAT_INSTRUCTIONS.format(tools_desc=tools_desc)}"

    def _build_user_prompt(
        self,
        message: str,
        profile: dict,
        history: list[Message],
        tool_results: list,
    ) -> str:
        """Construye el prompt del usuario con contexto completo."""
        parts = []

        # Perfil del usuario
        profile_text = json.dumps(profile, ensure_ascii=False, indent=2)
        parts.append(f"PERFIL DEL USUARIO:\n{profile_text}")

        # Historial reciente (últimos 5 mensajes)
        if history:
            recent = history[-5:]
            history_lines = []
            for m in recent:
                role = "Usuario" if m.role == "user" else "Coach" if m.role == "assistant" else "Sistema"
                history_lines.append(f"[{role}]: {m.content}")
            parts.append(f"HISTORIAL RECIENTE:\n" + "\n".join(history_lines))

        # Resultados de herramientas
        if tool_results:
            results_lines = []
            for r in tool_results:
                if r.success and r.data:
                    results_lines.append(f"[{r.tool_name}]: {json.dumps(r.data, ensure_ascii=False)}")
                elif not r.success:
                    results_lines.append(f"[{r.tool_name} ERROR]: {r.error}")
            if results_lines:
                parts.append(f"INFORMACIÓN OBTENIDA:\n" + "\n".join(results_lines))

        # Mensaje del usuario
        parts.append(f"MENSAJE DEL USUARIO:\n{message}")

        return "\n\n".join(parts)
