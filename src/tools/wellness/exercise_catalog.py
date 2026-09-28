"""Exercise Catalog Tool — búsqueda de ejercicios del catálogo."""

import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Exercise
from src.tools import ToolResult


class ExerciseCatalogTool:
    """Busca ejercicios del catálogo por nivel, tipo o condición médica.

    Precondiciones: Sesión SQLAlchemy válida con tabla exercises poblada.
    Postcondiciones: Retorna lista de ejercicios que cumplen los filtros.
    Efectos secundarios: None (solo lectura).
    """

    name = "exercise_catalog"
    description = "Busca ejercicios del catálogo por nivel, tipo o condición médica"

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def validate_args(self, **kwargs) -> bool:
        level = kwargs.get("level")
        if level is not None and (not isinstance(level, int) or level < 1 or level > 4):
            return False
        return True

    async def execute(self, **kwargs) -> ToolResult:
        """Ejecuta la búsqueda de ejercicios.

        Args:
            level: Nivel funcional (1=frágil, 2=activo, 3=muy activo, 4=deportista).
            keyword: Palabra clave para buscar en nombre/descripción.
            exclude_contraindications: Lista de contraindicaciones a excluir.

        Returns:
            ToolResult con data={"exercises": [...], "count": int}.
        """
        if not self.validate_args(**kwargs):
            return ToolResult(success=False, error="Invalid arguments", tool_name=self.name)

        try:
            level = kwargs.get("level")
            keyword = kwargs.get("keyword", "").lower()
            exclude = set(kwargs.get("exclude_contraindications", []))

            stmt = select(Exercise)
            result = await self._session.execute(stmt)
            exercises = result.scalars().all()

            filtered = []
            for ex in exercises:
                if level is not None and ex.level != level:
                    continue
                if keyword and keyword not in (ex.name or "").lower() and keyword not in (ex.description or "").lower():
                    continue
                if exclude and ex.contraindications:
                    contra = {x.strip() for x in ex.contraindications.split(",") if x.strip()}
                    if contra & exclude:
                        continue
                filtered.append({
                    "id": ex.id,
                    "name": ex.name,
                    "description": ex.description or "",
                    "level": ex.level,
                    "contraindications": ex.contraindications or "",
                    "video_url": ex.video_url or "",
                })

            return ToolResult(
                success=True,
                data={"exercises": filtered, "count": len(filtered)},
                tool_name=self.name,
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), tool_name=self.name)
