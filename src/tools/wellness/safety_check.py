"""Safety Check Tool — verificación de contraindicaciones."""

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.tools import ToolResult


class SafetyCheckTool:
    """Verifica si una actividad es segura dado el perfil del usuario.

    Precondiciones: Sesión SQLAlchemy válida con tablas users y exercises.
    Postcondiciones: Retorna evaluación de seguridad.
    Efectos secundarios: None (solo lectura).
    """

    name = "safety_check"
    description = "Verifica si una actividad es segura dado el perfil médico del usuario"

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def validate_args(self, **kwargs) -> bool:
        return "user_id" in kwargs and "activity" in kwargs

    async def execute(self, **kwargs) -> ToolResult:
        """Verifica seguridad de una actividad.

        Args:
            user_id: ID del usuario.
            activity: Descripción de la actividad a verificar.

        Returns:
            ToolResult con data={"safe": bool, "warnings": [...], "restrictions": [...]}.
        """
        if not self.validate_args(**kwargs):
            return ToolResult(success=False, error="user_id and activity required", tool_name=self.name)

        try:
            user_id = int(kwargs["user_id"])
            activity = kwargs["activity"].lower()

            # Get user restrictions
            result = await self._session.execute(
                text("SELECT health_profile, profile FROM users WHERE id = :uid"),
                {"uid": user_id},
            )
            row = result.fetchone()
            if not row:
                return ToolResult(success=False, error="User not found", tool_name=self.name)

            import json
            health = json.loads(row[0]) if isinstance(row[0], str) else (row[0] or {})
            profile = json.loads(row[1]) if isinstance(row[1], str) else (row[1] or {})

            restrictions = set(
                health.get("medical_restrictions", profile.get("medical_restrictions", []))
            )
            conditions = set(health.get("conditions", []))

            # Check against exercise contraindications
            result = await self._session.execute(
                text("SELECT name, contraindications FROM exercises")
            )
            exercises = result.fetchall()

            warnings = []
            matching_contras = set()

            for ex_name, contras in exercises:
                if not contras:
                    continue
                ex_contra = {x.strip().lower() for x in contras.split(",") if x.strip()}
                overlap = ex_contra & {r.lower() for r in restrictions}
                if overlap:
                    matching_contras.update(overlap)

            # Build warnings
            for restriction in restrictions:
                if restriction.lower() in activity:
                    warnings.append(f"La actividad '{activity}' puede conflicto con: {restriction}")

            if restrictions:
                warnings.append(f"El usuario tiene restricciones: {', '.join(restrictions)}")

            is_safe = len(warnings) == 0 or not any(
                w.startswith("La actividad") for w in warnings
            )

            return ToolResult(
                success=True,
                data={
                    "safe": is_safe,
                    "warnings": warnings,
                    "restrictions": list(restrictions),
                    "conditions": list(conditions),
                },
                tool_name=self.name,
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), tool_name=self.name)
