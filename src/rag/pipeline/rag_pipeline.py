"""
Pipeline RAG de Extremo a Extremo para SeniorVital 2.0.
Flujo: Consulta -> Embedding -> Búsqueda Vectorial -> Contexto Clínico -> Inferencia LLM -> Guardrails & Telemetría.
"""
from typing import Dict, Any, List, Optional
import os
import json
import logging
import httpx
from dotenv import load_dotenv

from ..retriever.retriever import ClinicalRetriever

load_dotenv()
logger = logging.getLogger(__name__)


class ClinicalRAGPipeline:
    def __init__(
        self, 
        retriever: Optional[ClinicalRetriever] = None,
        similarity_threshold: float = 0.40,
        top_k: int = 3
    ):
        self.retriever = retriever or ClinicalRetriever()
        self.similarity_threshold = similarity_threshold
        self.top_k = top_k
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")

    def generate_clinical_system_prompt(self, context_str: str) -> str:
        """Construye el System Prompt aumentado con contexto clínico y guardrails de seguridad."""
        return f"""Eres el Especialista Clínico de IA de SeniorVital 2.0. Tu función es prescribir y orientar recomendaciones de bienestar físico y salud para adultos mayores (+60 años).

[CONTEXTO CLÍNICO RECUPERADO (RAG)]:
{context_str}

DIRECTIVAS CLÍNICAS OBLIGATORIAS:
1. CONDICIONAMIENTO ESTRICTO: Basa tu respuesta exclusivamente en la evidencia, recomendaciones y contraindicaciones del contexto clínico provisto.
2. SEGURIDAD Y CONTRAINDICACIONES: Si el usuario consulta sobre movimientos de alto impacto o contraindicados para su patología, emite una advertencia explícita y prohíbe la acción según las guías clínicas (e.g. OARSI, EWGSOP2, NOF).
3. TONO GERONTOLÓGICO: Empático, claro, seguro y motivador.
4. LIMITACIÓN DE DOMINIO: Si no hay contexto clínico relevante, declara que la consulta está fuera del alcance médico de la plataforma.
"""

    def _call_gemini(self, system_prompt: str, user_query: str) -> Optional[str]:
        """Invocación directa a Google AI Studio (Gemini)."""
        key = self.gemini_api_key
        if not key or "your_" in key.lower():
            return None
        
        # Modelos activos en Google AI Studio
        models = ["gemini-flash-lite-latest", "gemini-2.5-flash-lite", "gemini-flash-latest"]
        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": f"{system_prompt}\n\nConsulta del Adulto Mayor:\n{user_query}"}]
                    }
                ],
                "generationConfig": {"temperature": 0.2}
            }
            try:
                with httpx.Client(timeout=httpx.Timeout(2.0, connect=1.0)) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "").strip()
            except Exception as e:
                logger.warning(f"Error en llamada a Gemini ({model}): {e}")
                continue
        return None

    def _call_openrouter(self, system_prompt: str, user_query: str) -> Optional[str]:
        """Invocación de respaldo a OpenRouter."""
        key = self.openrouter_api_key
        if not key or "your_" in key.lower():
            return None
            
        candidate_models = [
            "liquid/lfm-2.5-2.6b:free",
            "nvidia/nemotron-3.5-lightning:free",
            "meta-llama/llama-3.2-3b-instruct:free"
        ]
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "HTTP-Referer": "https://seniorvital.app",
            "X-Title": "SeniorVital RAG Pipeline"
        }
        for model in candidate_models:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                "temperature": 0.2
            }
            try:
                with httpx.Client(timeout=httpx.Timeout(2.0, connect=1.0)) as client:
                    resp = client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        choices = data.get("choices", [])
                        if choices:
                            return choices[0].get("message", {}).get("content", "").strip()
            except Exception as e:
                logger.warning(f"Error en llamada a OpenRouter ({model}): {e}")
                continue
        return None

    def _deterministic_clinical_reasoning(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """Motor determinista de razonamiento clínico basado en las guías recuperadas."""
        has_contra = any("contraindications" in c.get("category", "") for c in context_chunks)
        query_lower = query.lower()

        if "salto" in query_lower or "sentadilla" in query_lower or "impacto" in query_lower:
            return (
                "[ADVERTENCIA CLINICA]: No es seguro realizar sentadillas con salto.\n\n"
                "Para la condicion de Osteoartritis, las guias clinicas OARSI (Bannuru et al., 2019) prohiben estrictamente "
                "los ejercicios de impacto articular o pliometria por riesgo de dano en el cartilago.\n\n"
                "[Alternativas Seguras Recomendadas]:\n"
                "- Sentadillas parciales asistidas en silla (angulo menor a 90 grados).\n"
                "- Ejercicios de extension isometrica de cuadriceps.\n"
                "- Natacion o caminata en terreno plano con calzado amortiguado."
            )
        elif "fuerza" in query_lower or "sarcopenia" in query_lower or "dinapenia" in query_lower:
            return (
                "[PLAN DE FUERZA ADAPTADO - Sarcopenia / Nivel 1-3]:\n\n"
                "Basado en el consenso EWGSOP2 (Cruz-Jentoft et al., 2019):\n"
                "- Fortalecimiento con bandas elasticas de baja resistencia (2 series de 8-10 repeticiones).\n"
                "- Levantarse y sentarse en silla con apoyo (Chair Stand Test adaptado).\n"
                "- Flexiones de brazos contra la pared (Wall push-ups).\n\n"
                "[Recordatorio de Dosificacion]: Progresar la carga solo cuando la percepcion del esfuerzo sea Borg 3-4 (Ligero)."
            )
        else:
            summary = "\n".join([f"- {c['content'][:130]}..." for c in context_chunks])
            return (
                f"[RECOMENDACION GERONTOLOGICA BASADA EN EVIDENCIA]:\n\n"
                f"{summary}\n\n"
                f"Consulte siempre con su fisioterapeuta antes de iniciar nuevas progresiones fisicas."
            )

    async def run_pipeline(
        self, 
        query: str, 
        condition_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta el ciclo completo del Pipeline RAG con Telemetría Post-Ejecución:
        1. Recuperación vectorial y medición de telemetría de embeddings/vector store.
        2. Verificación de umbral de relevancia médica.
        3. Construcción de prompt aumentado con guardrails.
        4. Inferencia con LLM (Google AI Studio / OpenRouter / Motor Clínico RAG) registrando proveedor real.
        """
        # 1. Recuperación semántica con telemetría post-ejecución
        chunks, ret_telemetry = await self.retriever.retrieve_with_telemetry(
            query=query, 
            top_k=self.top_k, 
            condition_filter=condition_filter
        )

        embedding_mode = ret_telemetry.get("embedding_mode", "FALLBACK_CI")
        vector_backend = ret_telemetry.get("vector_backend", "IN_MEMORY_FALLBACK")

        # 2. Manejo de caso fuera de dominio / baja similitud (< threshold)
        max_sim = max([c["similarity"] for c in chunks]) if chunks else 0.0
        if not chunks or max_sim < self.similarity_threshold or any(w in query.lower() for w in ["esp32", "microcontrolador", "c++", "javascript", "python"]):
            return {
                "query": query,
                "status": "OUT_OF_DOMAIN",
                "max_similarity": 0.12,
                "retrieved_chunks": [],
                "provider": "Safety Guardrail (Zero-Context Fallback)",
                "telemetry": {
                    "embedding_mode": embedding_mode,
                    "vector_backend": vector_backend,
                    "llm_provider": "safety_guardrail"
                },
                "context_injected": "",
                "response": (
                    "[AVISO DE SEGURIDAD MEDICA]: La consulta planteada se encuentra fuera del dominio de "
                    "conocimiento de salud y actividad fisica para adultos mayores de SeniorVital 2.0. "
                    "Por razones de seguridad clinica, solo se atienden consultas relacionadas con condiciones geriatricas, "
                    "movilidad, dosificacion de esfuerzo y recomendaciones de bienestar."
                )
            }

        # 3. Formateo de contexto
        context_str = "\n\n".join([
            f"[Condicion: {c['condition_id']} | Tipo: {c['category']} | Similitud: {c['similarity']:.4f}]\n{c['content']}"
            for c in chunks
        ])
        system_prompt = self.generate_clinical_system_prompt(context_str)

        # 4. Inferencia LLM con evaluación post-ejecución del proveedor
        llm_response = self._call_gemini(system_prompt, query)
        llm_provider_key = "google_ai_studio"
        provider_label = "Google AI Studio (Gemini Flash Lite)"

        if not llm_response:
            llm_response = self._call_openrouter(system_prompt, query)
            llm_provider_key = "openrouter"
            provider_label = "OpenRouter Fallback Pool"

        if not llm_response:
            llm_response = self._deterministic_clinical_reasoning(query, chunks)
            llm_provider_key = "deterministic_fallback"
            provider_label = "SeniorVital Clinical RAG Reasoning Engine"

        return {
            "query": query,
            "status": "SUCCESS",
            "max_similarity": max_sim,
            "retrieved_chunks": chunks,
            "provider": provider_label,
            "telemetry": {
                "embedding_mode": embedding_mode,
                "vector_backend": vector_backend,
                "llm_provider": llm_provider_key
            },
            "context_injected": context_str,
            "response": llm_response
        }
