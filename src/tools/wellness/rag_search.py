"""RAG Search Tool — consulta la base de conocimiento RAG."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from src.tools import ToolResult


class RAGSearchTool:
    """Consulta la base de conocimiento de bienestar para adultos mayores.

    Precondiciones: RAG pipeline inicializado (ChromaDB + embeddings).
    Postcondiciones: Retorna respuesta basada en conocimiento recuperado.
    Efectos secundarios: None (solo lectura del vector store).
    """

    name = "rag_search"
    description = "Consulta la base de conocimiento de bienestar para adultos mayores"

    def __init__(self, rag_pipeline=None) -> None:
        self._pipeline = rag_pipeline

    def validate_args(self, **kwargs) -> bool:
        return "query" in kwargs and isinstance(kwargs["query"], str) and len(kwargs["query"].strip()) > 0

    async def execute(self, **kwargs) -> ToolResult:
        """Consulta el pipeline RAG.

        Args:
            query: Pregunta del usuario.
            macrodomain: Dominio opcional (A-F) para filtrar.
            k: Número de chunks a recuperar (default: 5).

        Returns:
            ToolResult con data={"answer": "...", "sources": [...], "agent": "..."}.
        """
        if not self.validate_args(**kwargs):
            return ToolResult(success=False, error="query required", tool_name=self.name)

        if self._pipeline is None:
            return ToolResult(
                success=False,
                error="RAG pipeline not available",
                tool_name=self.name,
            )

        try:
            query = kwargs["query"]
            macrodomain = kwargs.get("macrodomain")
            k = kwargs.get("k", 5)

            # Si el pipeline expone process_query (ej. pipeline mockeado o legacy)
            if hasattr(self._pipeline, "process_query"):
                result = await self._pipeline.process_query(
                    query, macrodomain=macrodomain
                )
                return ToolResult(
                    success=True,
                    data={
                        "answer": result.get("answer", ""),
                        "sources": result.get("sources", []),
                        "agent": result.get("agent", ""),
                        "macrodomain": result.get("macrodomain", ""),
                        "warnings": result.get("warnings", []),
                        "telemetry": result.get("telemetry", {}),
                    },
                    tool_name=self.name,
                )

            # Si el pipeline expone retrieve_with_telemetry (ClinicalRetriever de Sprint 1)
            if hasattr(self._pipeline, "retrieve_with_telemetry"):
                chunks, telemetry = await self._pipeline.retrieve_with_telemetry(
                    query=query, top_k=k
                )
                answer_summary = " ".join([c.get("content", "") for c in chunks])
                return ToolResult(
                    success=True,
                    data={
                        "answer": answer_summary,
                        "sources": [c.get("condition_id", "GEN") for c in chunks],
                        "agent": "ClinicalRetriever",
                        "macrodomain": macrodomain or "A",
                        "warnings": [],
                        "telemetry": telemetry,
                        "chunks": chunks,
                    },
                    tool_name=self.name,
                )

            # Si el pipeline expone run_pipeline (ClinicalRAGPipeline)
            if hasattr(self._pipeline, "run_pipeline"):
                res = await self._pipeline.run_pipeline(query=query)
                return ToolResult(
                    success=True,
                    data={
                        "answer": res.get("response", ""),
                        "sources": [c.get("condition_id", "GEN") for c in res.get("retrieved_chunks", [])],
                        "agent": res.get("provider", "ClinicalRAGPipeline"),
                        "macrodomain": macrodomain or "A",
                        "warnings": [],
                        "telemetry": res.get("telemetry", {}),
                        "chunks": res.get("retrieved_chunks", []),
                    },
                    tool_name=self.name,
                )

            return ToolResult(
                success=False,
                error="Unsupported RAG pipeline interface",
                tool_name=self.name,
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"RAG search error: {str(e)}",
                tool_name=self.name,
            )
