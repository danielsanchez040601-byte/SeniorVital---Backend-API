"""
Pipeline de Generación Aumentada por Recuperación (RAG) para Prescripción Segura.
"""
from typing import Dict, Any, List, Optional
from ..retriever.retriever import ClinicalRetriever
from sqlalchemy.ext.asyncio import AsyncSession


class ClinicalRAGPipeline:
    def __init__(self, retriever: Optional[ClinicalRetriever] = None):
        self.retriever = retriever or ClinicalRetriever()

    async def assemble_context(self, session: AsyncSession, user_profile: Dict[str, Any]) -> str:
        """Construye el bloque de contexto clínico a partir del perfil del adulto mayor."""
        pathologies = user_profile.get("conditions", [])
        context_blocks = []

        for p_id in pathologies:
            chunks = await self.retriever.retrieve(
                session=session,
                query=f"Reglas de ejercicio y contraindicaciones para {p_id}",
                top_k=2,
                pathology_filter=p_id
            )
            for ch in chunks:
                context_blocks.append(ch["content"])

        if not context_blocks:
            return "REGLAS GENERALES: Adulto mayor de 60 años. Intensidad leve a moderada (RPE 3-5), sin impacto articular."

        return "\n---\n".join(context_blocks)

    def generate_clinical_system_prompt(self, context_str: str) -> str:
        """Genera el system prompt enriquecido con RAG para el LLM."""
        return (
            "Eres el Asistente Clínico de SeniorVital, especialista en gerontología y actividad física adaptada.\n"
            "INSTRUCCIONES ESTRICTAS:\n"
            "1. Prescribe únicamente ejercicios compatibles con las condiciones del paciente.\n"
            "2. Respeta estrictamente las contraindicaciones del contexto médico recuperado.\n"
            "3. No recomiendes fármacos ni dosis médicas.\n\n"
            f"[CONTEXTO CLÍNICO RECUPERADO (RAG)]:\n{context_str}\n"
        )
