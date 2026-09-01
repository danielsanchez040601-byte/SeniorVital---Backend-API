"""
Cliente Unificado de Inferencia LLM — SeniorVital 2.0
Integra Google AI Studio (Gemini Flash Lite / Gemini 2.5 Flash), OpenRouter y Motor Clínico de Respaldo.
"""
import os
import json
import re
import httpx
from typing import Optional, Dict, Any

try:
    from src.api.config import settings
except ImportError:
    try:
        from ..api.config import settings
    except ImportError:
        class DummySettings:
            GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
            GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
            OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
            DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "gemini-flash-lite-latest")
        settings = DummySettings()


def _clean_json_response(raw_text: str) -> Optional[Dict[str, Any]]:
    """Extrae y parsea un diccionario JSON desde texto plano o bloques markdown."""
    if not raw_text:
        return None
    
    # 1. Intento directo
    try:
        return json.loads(raw_text.strip())
    except Exception:
        pass

    # 2. Extracción de bloques markdown ```json ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    # 3. Extracción de llave a llave {...}
    match_braces = re.search(r"(\{.*\})", raw_text, re.DOTALL)
    if match_braces:
        try:
            return json.loads(match_braces.group(1))
        except Exception:
            pass

    return None


async def call_google_ai_studio_json(system_prompt: str, user_prompt: str, timeout: float = 12.0) -> Optional[Dict[str, Any]]:
    """Inferencia con Google AI Studio (Gemini Flash Lite con respuesta JSON forzada)."""
    api_key = getattr(settings, "GEMINI_API_KEY", None) or getattr(settings, "GOOGLE_API_KEY", None) or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key or "your_" in api_key.lower():
        return None

    # Modelos soportados y activos en Google AI Studio
    models = ["gemini-flash-lite-latest", "gemini-2.5-flash-lite", "gemini-flash-latest", "gemini-2.5-flash", "gemini-pro-latest"]
    async with httpx.AsyncClient(timeout=timeout) as client:
        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": f"{system_prompt}\n\nSolicitud del Usuario:\n{user_prompt}"}]
                    }
                ],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "temperature": 0.2
                }
            }
            try:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        content_parts = candidates[0].get("content", {}).get("parts", [])
                        if content_parts:
                            text_out = content_parts[0].get("text", "")
                            parsed = _clean_json_response(text_out)
                            if parsed and ("exercises" in parsed or "warmup" in parsed or "rutina_ejercicio" in parsed):
                                print(f"🤖 [LLM Inferencia] Rutina generada con éxito vía Google AI Studio ({model}).")
                                # Normalizar claves si vienen anidadas
                                if "rutina_ejercicio" in parsed and "exercises" not in parsed:
                                    parsed["exercises"] = parsed["rutina_ejercicio"].get("ejercicios", parsed["rutina_ejercicio"].get("exercises", []))
                                    parsed["warmup"] = parsed["rutina_ejercicio"].get("calentamiento", parsed["rutina_ejercicio"].get("warmup", []))
                                return parsed
            except Exception as e:
                continue
    return None


async def call_openrouter_json(system_prompt: str, user_prompt: str, timeout: float = 12.0) -> Optional[Dict[str, Any]]:
    """Inferencia de respaldo con OpenRouter."""
    api_key = getattr(settings, "OPENROUTER_API_KEY", None) or os.getenv("OPENROUTER_API_KEY")
    if not api_key or "your_" in api_key.lower():
        return None

    candidate_models = [
        "liquid/lfm-2.5-2.6b:free",
        "nvidia/nemotron-3.5-lightning:free",
        "inclusionai/ling-3.0-flash-fin:free",
        "meta-llama/llama-3.2-3b-instruct:free"
    ]
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://seniorvital.app",
        "X-Title": "SeniorVital Gerontological AI",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        for model in candidate_models:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            }
            try:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        parsed = _clean_json_response(content)
                        if parsed and ("exercises" in parsed or "warmup" in parsed):
                            print(f"🌐 [LLM Inferencia] Rutina generada con éxito vía OpenRouter ({model}).")
                            return parsed
            except Exception as e:
                continue
    return None


async def call_llm_json(system_prompt: str, user_prompt: str, timeout: float = 14.0) -> Optional[Dict[str, Any]]:
    """
    Función principal de inferencia en cascada:
    1. Intenta Google AI Studio (Gemini).
    2. Si falla o no hay key, intenta OpenRouter.
    3. Si ambos fallan o no hay conexión externa, retorna None para degradación elegante.
    """
    # 1. Google AI Studio
    result = await call_google_ai_studio_json(system_prompt, user_prompt, timeout=timeout)
    if result:
        return result

    # 2. OpenRouter
    result = await call_openrouter_json(system_prompt, user_prompt, timeout=timeout)
    if result:
        return result

    return None
