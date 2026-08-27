import os
import json
import httpx
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from ..config import settings

# 1. Modelos principales de Google AI Studio (Activos y verificados con GEMINI_API_KEY)
PRIMARY_GEMINI_MODELS = [
    "gemini-3.6-flash",  # Máxima prioridad: Modo JSON nativo y alta velocidad
    "gemini-3.5-flash"   # Respaldo inmediato en Google AI Studio
]

# 2. Modelos de respaldo activos y verificados en OpenRouter (Solo si Google AI Studio falla)
OPENROUTER_FALLBACK_MODELS = [
    "openrouter/free",                # Enrutador dinámico oficial de modelos gratuitos
    "google/gemma-4-31b-it:free",      # Google Gemma 31B (Activo y funcional)
    "google/gemma-4-26b-a4b-it:free",  # Google Gemma 26B
    "z-ai/glm-5.2:free",               # GLM 5.2
    "minimax/minimax-m3:free"          # MiniMax M3
]


async def call_llm_text(system_prompt: str, user_prompt: str, timeout: float = 12.0) -> Optional[str]:
    """
    Invoca el LLM con arquitectura de Prioridad y Fallback Resiliente:
    1. Proveedor Principal: Google AI Studio (gemini-3.6-flash / gemini-flash-latest con GEMINI_API_KEY).
    2. Proveedor de Respaldo: Cadena iterativa de modelos activos en OpenRouter (OPENROUTER_API_KEY).
    3. Retorna None si todos fallan para activar la degradación clínica elegante.
    """
    gemini_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY

    # -------------------------------------------------------------------------
    # INTENTO 1: Google AI Studio (gemini-3.6-flash como prioridad máxima)
    # -------------------------------------------------------------------------
    if gemini_key:
        for gem_model in PRIMARY_GEMINI_MODELS:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{gem_model}:generateContent?key={gemini_key}"
                full_text = f"{system_prompt}\n\nConsulta del Usuario:\n{user_prompt}"
                payload = {
                    "contents": [{"parts": [{"text": full_text}]}]
                }
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])
                        if parts and "text" in parts[0]:
                            print(f"[LLM Engine] Respuesta exitosa con Google AI Studio ({gem_model})")
                            return parts[0]["text"].strip()
                    else:
                        print(f"[Google AI Studio] HTTP {resp.status_code} en {gem_model}: {resp.text[:120]}")
            except Exception as gem_err:
                print(f"[Google AI Studio Fallback] Error en {gem_model}: {gem_err}")

    # -------------------------------------------------------------------------
    # INTENTO 2 EN ADELANTE: Cadena de Modelos de Respaldo en OpenRouter
    # -------------------------------------------------------------------------
    if settings.OPENROUTER_API_KEY:
        print("[LLM Engine] Activando cadena de respaldo OpenRouter...")
        for model_name in OPENROUTER_FALLBACK_MODELS:
            try:
                llm = ChatOpenAI(
                    api_key=settings.OPENROUTER_API_KEY,
                    base_url="https://openrouter.ai/api/v1",
                    model=model_name,
                    temperature=0.7,
                    timeout=timeout,
                    default_headers={
                        "HTTP-Referer": "https://seniorvital-backend.onrender.com",
                        "X-Title": "SeniorVital Wellness Coach"
                    }
                )
                resp = await llm.ainvoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ])
                if resp and resp.content:
                    print(f"[LLM Engine] Respuesta exitosa con OpenRouter ({model_name})")
                    return str(resp.content).strip()
            except Exception as or_err:
                print(f"[OpenRouter Fallback] Modelo {model_name} fallo: {or_err}")

    print("[LLM Engine] Todos los proveedores de IA upstream fallaron o estan saturados.")
    return None


async def call_llm_json(system_prompt: str, user_prompt: str, timeout: float = 14.0) -> Optional[Dict[str, Any]]:
    """
    Invoca el LLM solicitando y validando una respuesta estructurada JSON:
    1. Intenta primero con Google AI Studio (gemini-3.6-flash con response_mime_type: application/json).
    2. Itera sobre los modelos de respaldo válidos en OpenRouter.
    3. Retorna dict estructurado o None si falla.
    """
    gemini_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY

    # -------------------------------------------------------------------------
    # INTENTO 1: Google AI Studio Directo con modo JSON nativo
    # -------------------------------------------------------------------------
    if gemini_key:
        for gem_model in PRIMARY_GEMINI_MODELS:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{gem_model}:generateContent?key={gemini_key}"
                full_text = f"{system_prompt}\n\nDatos del Usuario:\n{user_prompt}"
                payload = {
                    "contents": [{"parts": [{"text": full_text}]}],
                    "generationConfig": {"response_mime_type": "application/json"}
                }
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                        data = json.loads(raw_text)
                        if isinstance(data, dict) and "exercises" in data:
                            print(f"[LLM Engine JSON] Rutina generada con Google AI Studio ({gem_model})")
                            return data
            except Exception as gem_err:
                print(f"[Google AI Studio JSON] Error en {gem_model}: {gem_err}")

    # -------------------------------------------------------------------------
    # INTENTO 2 EN ADELANTE: OpenRouter Fallback Chain
    # -------------------------------------------------------------------------
    if settings.OPENROUTER_API_KEY:
        print("[LLM Engine JSON] Activando cadena de respaldo OpenRouter para JSON...")
        for model_name in OPENROUTER_FALLBACK_MODELS:
            try:
                llm = ChatOpenAI(
                    api_key=settings.OPENROUTER_API_KEY,
                    base_url="https://openrouter.ai/api/v1",
                    model=model_name,
                    temperature=0.4,
                    timeout=timeout,
                    default_headers={
                        "HTTP-Referer": "https://seniorvital-backend.onrender.com",
                        "X-Title": "SeniorVital Routine Generator"
                    }
                )
                resp = await llm.ainvoke([
                    SystemMessage(content=system_prompt + "\nIMPORTANTE: Responde UNICAMENTE en formato JSON valido."),
                    HumanMessage(content=user_prompt)
                ])
                content = str(resp.content).strip()
                if content.startswith("```json"):
                    content = content.split("```json")[1].split("```")[0].strip()
                elif content.startswith("```"):
                    content = content.split("```")[1].split("```")[0].strip()
                
                data = json.loads(content)
                if isinstance(data, dict) and "exercises" in data:
                    print(f"[LLM Engine JSON] Rutina generada con OpenRouter ({model_name})")
                    return data
            except Exception as or_err:
                print(f"[OpenRouter JSON] Fallo modelo {model_name}: {or_err}")

    return None
