"""Get Progress Tool — consulta de progreso y proyecciones."""

from datetime import date, timedelta
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.tools import ToolResult


class GetProgressTool:
    """Obtiene insights y proyecciones de progreso del usuario.

    Precondiciones: Sesión SQLAlchemy válida con tablas projections y tracking.
    Postcondiciones: Retorna insights y resumen de actividad.
    Efectos secundarios: None (solo lectura).
    """

    name = "get_progress"
    description = "Obtiene insights y proyecciones de progreso del usuario"

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def validate_args(self, **kwargs) -> bool:
        return "user_id" in kwargs

    async def execute(self, **kwargs) -> ToolResult:
        """Consulta progreso del usuario.

        Args:
            user_id: ID del usuario.
            weeks: Número de semanas hacia atrás (default: 4).

        Returns:
            ToolResult con data={"insights": [...], "weekly_activity": [...], "total_sessions": int}.
        """
        if not self.validate_args(**kwargs):
            return ToolResult(success=False, error="user_id required", tool_name=self.name)

        try:
            user_id = int(kwargs["user_id"])
            weeks = kwargs.get("weeks", 4)
            since = date.today() - timedelta(weeks=weeks)

            # Insights from projections
            result = await self._session.execute(
                text("""
                    SELECT week_start, insight_text, estimated_level
                    FROM projections
                    WHERE user_id = :uid AND week_start >= :since
                    ORDER BY week_start DESC
                """),
                {"uid": user_id, "since": since},
            )
            insights = [
                {"week": str(r[0]), "insight": r[1], "level": r[2]}
                for r in result.fetchall()
            ]

            # Weekly session count
            result = await self._session.execute(
                text("""
                    SELECT DATE_TRUNC('week', scheduled_date)::date as week,
                           COUNT(*) as sessions
                    FROM workout_sessions
                    WHERE user_id = :uid AND scheduled_date >= :since
                    GROUP BY week ORDER BY week DESC
                """),
                {"uid": user_id, "since": since},
            )
            weekly = [
                {"week": str(r[0]), "sessions": r[1]}
                for r in result.fetchall()
            ]

            # Total sessions
            result = await self._session.execute(
                text("SELECT COUNT(*) FROM workout_sessions WHERE user_id = :uid"),
                {"uid": user_id},
            )
            total = result.scalar() or 0

            return ToolResult(
                success=True,
                data={"insights": insights, "weekly_activity": weekly, "total_sessions": total},
                tool_name=self.name,
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), tool_name=self.name)
