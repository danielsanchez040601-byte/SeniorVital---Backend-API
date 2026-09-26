"""Get Habits Tool — consulta de hábitos diarios del usuario."""

from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Base
from src.tools import ToolResult


class _Habit(Base):
    """Mapping temporal para consulta de hábitos (tabla habits)."""
    __tablename__ = "habits"
    __table_args__ = {"extend_existing": True}
    from sqlalchemy import Column, Integer, Date, Numeric, Text
    from sqlalchemy.sql import func
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    date = Column(Date)
    water_intake_glasses = Column(Integer, default=0)
    sleep_hours = Column(Numeric(3, 1))
    created_at = Column(Date, server_default=func.now())


class GetHabitsTool:
    """Obtiene el registro de hábitos (agua, sueño) del usuario.

    Precondiciones: Sesión SQLAlchemy válida con tabla habits poblada.
    Postcondiciones: Retorna lista de hábitos diarios.
    Efectos secundarios: None (solo lectura).
    """

    name = "get_habits"
    description = "Obtiene el registro de hábitos (agua, sueño) del usuario de los últimos días"

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def validate_args(self, **kwargs) -> bool:
        return "user_id" in kwargs

    async def execute(self, **kwargs) -> ToolResult:
        """Ejecuta la consulta de hábitos.

        Args:
            user_id: ID del usuario.
            days: Número de días hacia atrás (default: 7).

        Returns:
            ToolResult con data={"habits": [{date, water, sleep}, ...]}.
        """
        if not self.validate_args(**kwargs):
            return ToolResult(success=False, error="user_id required", tool_name=self.name)

        try:
            user_id = int(kwargs["user_id"])
            days = kwargs.get("days", 7)
            since = date.today() - timedelta(days=days)

            stmt = (
                select(_Habit)
                .where(_Habit.user_id == user_id, _Habit.date >= since)
                .order_by(_Habit.date.desc())
            )
            result = await self._session.execute(stmt)
            habits = result.scalars().all()

            return ToolResult(
                success=True,
                data={
                    "habits": [
                        {
                            "date": h.date.isoformat() if h.date else None,
                            "water_glasses": h.water_intake_glasses or 0,
                            "sleep_hours": float(h.sleep_hours) if h.sleep_hours else None,
                        }
                        for h in habits
                    ],
                    "count": len(habits),
                },
                tool_name=self.name,
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), tool_name=self.name)
