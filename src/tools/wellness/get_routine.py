"""Get Routine Tool — consulta de la rutina activa del día."""

import json
from datetime import date
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.tools import ToolResult


class GetRoutineTool:
    """Obtiene la rutina activa del día de hoy para un usuario.

    Precondiciones: Sesión SQLAlchemy válida con tabla routines.
    Postcondiciones: Retorna la rutina o error si no existe.
    Efectos secundarios: None (solo lectura).
    """

    name = "get_routine"
    description = "Obtiene la rutina activa del día de hoy para un usuario"

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def validate_args(self, **kwargs) -> bool:
        return "user_id" in kwargs

    async def execute(self, **kwargs) -> ToolResult:
        """Consulta la rutina del día.

        Args:
            user_id: ID del usuario.

        Returns:
            ToolResult con data={"routine": {...}} o error si no existe.
        """
        if not self.validate_args(**kwargs):
            return ToolResult(success=False, error="user_id required", tool_name=self.name)

        try:
            user_id = int(kwargs["user_id"])
            today = date.today()

            result = await self._session.execute(
                text("""
                    SELECT id, user_id, date, exercises, warmup, generated_by, created_at
                    FROM routines
                    WHERE user_id = :uid AND date = :d AND active = true
                    LIMIT 1
                """),
                {"uid": user_id, "d": today},
            )
            row = result.fetchone()

            if not row:
                return ToolResult(
                    success=False,
                    error="No routine for today",
                    tool_name=self.name,
                )

            exercises = row[3]
            if isinstance(exercises, str):
                exercises = json.loads(exercises)

            return ToolResult(
                success=True,
                data={
                    "routine": {
                        "id": str(row[0]),
                        "user_id": str(row[1]),
                        "date": str(row[2]),
                        "exercises": exercises,
                        "warmup": row[4],
                        "generated_by": row[5],
                    }
                },
                tool_name=self.name,
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), tool_name=self.name)
