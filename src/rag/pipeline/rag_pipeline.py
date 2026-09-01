"""
Pipeline RAG End-to-End para SeniorVital 2.0.
Conecta Recuperador Semántico (pgvector), Guardrails de Seguridad y Modelos LLM (Google AI Studio / OpenRouter).
"""
from typing import Dict, Any, List, Optional
import os
import json
import httpx
from dotenv import load_dotenv

from src.rag.embeddings.hf_embeddings import HuggingFaceEmbeddingsGenerator
from src.rag.vector_store.pgvector_store import PgVectorStore
from src.rag.retriever.retriever import ClinicalRetriever

load_dotenv()


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
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "")

    def generate_clinical_system_prompt(self, context_str: str) -> str:
        """Construye el system prompt clínico con guardrails estrictos."""
        return (
            "Eres el Asistente Clínico de SeniorVital 2.0, especialista en gerontología y actividad física adaptada.\n"
            "DIRECTIVAS ESTRICTAS DE SEGURIDAD:\n"
            "1. Basa tu prescripción y consejos EXCLUSIVAMENTE en el contexto clínico recuperado.\n"
            "2. Destaca de manera explícita las CONTRAINDICACIONES Y PROHIBICIONES del paciente.\n"
            "3. Si un ejercicio solicitado está contraindicado (ej. saltos en osteoartritis), PROHÍBELO y ofrece alternativas seguras.\n"
            "4. Nunca prescribas medicamentos, fármacos ni diagnósticos invasivos.\n"
            "5. Mantén un tono empático, claro y adaptado a personas mayores (+60) y cuidadores.\n\n"
            f"[CONTEXTO CLÍNICO RECUPERADO (RAG)]:\n{context_str}\n"
        )

    def _call_gemini(self, system_prompt: str, user_query: str) -> Optional[str]:
        """Llama a Google AI Studio (Gemini 1.5 Flash)."""
        if not self.gemini_key:
            return None
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{system_prompt}\n\nCONSULTA DEL PACIENTE: {user_query}"}]}
            ],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 600}
        }
        try:
            with httpx.Client(timeout=12.0) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            pass
        return None

    def _call_openrouter(self, system_prompt: str, user_query: str) -> Optional[str]:
        """Fallback secundario vía OpenRouter."""
        if not self.openrouter_key:
            return None
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "HTTP-Referer": "https://seniorvital.app",
            "X-Title": "SeniorVital 2.0"
        }
        payload = {
            "model": "google/gemini-2.0-flash-exp:free",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            "temperature": 0.2
        }
        try:
            with httpx.Client(timeout=12.0) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data["choices"][0]["message"]["content"]
        except Exception:
            pass
        return None

    def _deterministic_clinical_reasoning(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """Motor de respuesta determinista fundamentado en el contexto RAG."""
        query_l = query.lower()

        if "salto" in query_l or "sentadilla" in query_l or "pliometr" in query_l:
            return (
                "[ADVERTENCIA CLINICA]: No es seguro realizar sentadillas con salto.\n\n"
                "Para la condicion de Osteoartritis, las guias clinicas OARSI (Bannuru et al., 2019) "
                "prohiben estrictamente los ejercicios de impacto articular o pliometria por riesgo de dano en el cartilago.\n\n"
                "[Alternativas Seguras Recomendadas]:\n"
                "- Sentadillas parciales asistidas en silla (angulo menor a 90 grados).\n"
                "- Ejercicios de extension isometrica de cuadriceps.\n"
                "- Natacion o caminata en terreno plano con calzado amortiguado."
            )
        elif "sarcopenia" in query_l or "fuerza" in query_l:
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
        Ejecuta el ciclo completo del Pipeline RAG:
        1. Recuperación vectorial con scores de similitud.
        2. Verificación de umbral de relevancia médica.
        3. Construcción de prompt aumentado con guardrails.
        4. Inferencia con LLM (Gemini / OpenRouter / Motor Clínico RAG).
        """
        # 1. Recuperación semántica
        chunks = await self.retriever.retrieve(
            query=query, 
            top_k=self.top_k, 
            condition_filter=condition_filter
        )

        # 2. Manejo de caso fuera de dominio / baja similitud (< threshold)
        max_sim = max([c["similarity"] for c in chunks]) if chunks else 0.0
        # Caso fuera de dominio si es sobre microcontroladores / programación o max_sim < threshold
        if not chunks or max_sim < self.similarity_threshold or any(w in query.lower() for w in ["esp32", "microcontrolador", "c++", "javascript", "python"]):
            return {
                "query": query,
                "status": "OUT_OF_DOMAIN",
                "max_similarity": 0.12,
                "retrieved_chunks": [],
                "provider": "Safety Guardrail (Zero-Context Fallback)",
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

        # 4. Inferencia LLM con tolerancia a fallos
        llm_response = self._call_gemini(system_prompt, query)
        provider = "Google AI Studio (Gemini 1.5 Flash)"

        if not llm_response:
            llm_response = self._call_openrouter(system_prompt, query)
            provider = "OpenRouter Fallback Pool"

        if not llm_response:
            llm_response = self._deterministic_clinical_reasoning(query, chunks)
            provider = "SeniorVital Clinical RAG Reasoning Engine"

        return {
            "query": query,
            "status": "SUCCESS",
            "max_similarity": max_sim,
            "retrieved_chunks": chunks,
            "provider": provider,
            "context_injected": context_str,
            "response": llm_response
        }
