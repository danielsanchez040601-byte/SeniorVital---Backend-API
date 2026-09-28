"""Generate Routine Tool — delega a WellnessAgent para generar rutinas."""

from src.tools import ToolResult


class GenerateRoutineTool:
    """Genera una rutina de ejercicios personalizada para el día de hoy.

    Precondiciones: WellnessAgent inicializado con LLM y repositorios.
    Postcondiciones: Rutina guardada en BD y retornada.
    Efectos secundarios: INSERT en tabla routines.
    """

    name = "generate_routine"
    description = "Genera una rutina de ejercicios personalizada para el día de hoy"

    def __init__(self, agent) -> None:
        self._agent = agent

    def validate_args(self, **kwargs) -> bool:
        return "user_id" in kwargs

    async def execute(self, **kwargs) -> ToolResult:
        """Ejecuta la generación de rutina.

        Args:
            user_id: ID del usuario.
            force: Si True, regenera aunque ya exista (default: False).

        Returns:
            ToolResult con data={"routine": {...}, "generated_by": "ollama|fallback"}.
        """
        if not self.validate_args(**kwargs):
            return ToolResult(success=False, error="user_id required", tool_name=self.name)

        try:
            user_id = int(kwargs["user_id"])
            force = kwargs.get("force", False)
            result = await self._agent.generate_routine(user_id, force=force)
            return ToolResult(
                success=True,
                data={"routine": result.to_dict(), "generated_by": result.generated_by},
                tool_name=self.name,
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), tool_name=self.name)
