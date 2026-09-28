"""Log Habit Tool — registro de hábitos diarios."""

from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.tools import ToolResult


class LogHabitTool:
    """Registra un hábito diario (agua o sueño).

    Precondiciones: Sesión SQLAlchemy válida.
    Postcondiciones: Hábito insertado o actualizado en BD.
    Efectos secundarios: INSERT/UPDATE en tabla habits.
    """

    name = "log_habit"
    description = "Registra un hábito diario (consumo de agua en vasos o horas de sueño)"

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def validate_args(self, **kwargs) -> bool:
        if "user_id" not in kwargs or "habit_type" not in kwargs:
            return False
        if kwargs["habit_type"] not in ("water", "sleep"):
            return False
        if "value" not in kwargs:
            return False
        return True

    async def execute(self, **kwargs) -> ToolResult:
        """Registra un hábito.

        Args:
            user_id: ID del usuario.
            habit_type: "water" (vasos) | "sleep" (horas).
            value: Valor a registrar.

        Returns:
            ToolResult con data={"logged": True, "date": "...", "type": "...", "value": ...}.
        """
        if not self.validate_args(**kwargs):
            return ToolResult(success=False, error="user_id, habit_type, value required", tool_name=self.name)

        try:
            user_id = int(kwargs["user_id"])
            habit_type = kwargs["habit_type"]
            value = float(kwargs["value"])
            today = date.today()

            # Use raw SQL via the session's connection for simplicity
            from sqlalchemy import text
            if habit_type == "water":
                await self._session.execute(
                    text("""
                        INSERT INTO habits (user_id, date, water_intake_glasses)
                        VALUES (:uid, :d, :val)
                        ON CONFLICT (user_id, date)
                        DO UPDATE SET water_intake_glasses = :val, updated_at = NOW()
                    """),
                    {"uid": user_id, "d": today, "val": int(value)},
                )
            else:  # sleep
                await self._session.execute(
                    text("""
                        INSERT INTO habits (user_id, date, sleep_hours)
                        VALUES (:uid, :d, :val)
                        ON CONFLICT (user_id, date)
                        DO UPDATE SET sleep_hours = :val, updated_at = NOW()
                    """),
                    {"uid": user_id, "d": today, "val": value},
                )
            await self._session.flush()

            return ToolResult(
                success=True,
                data={"logged": True, "date": today.isoformat(), "type": habit_type, "value": value},
                tool_name=self.name,
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), tool_name=self.name)
