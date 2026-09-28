"""Tools module — protocols para herramientas del agente.

Este módulo define las interfaces (protocols) para herramientas que el agente
puede invocar. Las implementaciones concretas se crearán en S2-04.

Ejemplo de uso::

    from src.tools import Tool, ToolResult

    class WeatherTool:
        name = "weather"
        description = "Obtiene el clima actual de una ciudad"

        async def execute(self, **kwargs) -> ToolResult:
            city = kwargs.get("city", "")
            return ToolResult(success=True, data={"temp": 22}, tool_name=self.name)

        def validate_args(self, **kwargs) -> bool:
            return "city" in kwargs and isinstance(kwargs["city"], str)

    tool: Tool = WeatherTool()
"""

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class ToolResult:
    """Resultado de la ejecución de una herramienta.

    Attributes:
        success: Si la ejecución fue exitosa.
        data: Datos retornados por la herramienta (None si falló).
        error: Mensaje de error si falló (None si fue exitoso).
        tool_name: Nombre de la herramienta ejecutada.
    """

    success: bool
    data: dict | None = None
    error: str | None = None
    tool_name: str = ""


class ToolExecutionError(Exception):
    """Se lanza cuando la ejecución de una herramienta falla de forma irrecuperable.

    Attributes:
        tool_name: Nombre de la herramienta que falló.
        original_error: Excepción original que causó el fallo.
    """

    def __init__(self, tool_name: str, message: str, original_error: Exception | None = None) -> None:
        super().__init__(f"Tool '{tool_name}' failed: {message}")
        self.tool_name = tool_name
        self.original_error = original_error


@runtime_checkable
class Tool(Protocol):
    """Contrato para herramientas del agente.

    Precondiciones:
        - La herramienta debe estar configurada con sus dependencias
          (API keys, clientes HTTP, conexiones a BD, etc.).
        - validate_args() debe retornar True antes de execute().

    Postcondiciones:
        - execute() retorna ToolResult con success=True y data poblado,
          o success=False y error descriptivo.
        - La herramienta NO debe modificar estado global del agente.

    Efectos secundarios:
        - Las herramientas PUEDEN tener efectos secundarios (escritura a BD,
          llamadas HTTP, archivos en disco, etc.). Cada herramienta documenta
          sus efectos en la descripción de la clase.
        - Las herramientas NO deben tener efectos colaterales no documentados.

    Excepciones:
        - ToolExecutionError: Si la ejecución falla de forma irrecuperable.
        - ValueError: Si validate_args() retorna False y se llama a execute().
    """

    name: str
    description: str

    async def execute(self, **kwargs) -> ToolResult:
        """Ejecuta la herramienta con los argumentos proporcionados.

        Args:
            **kwargs: Argumentos específicos de cada herramienta.
                      Cada herramienta define sus propios argumentos.

        Returns:
            ToolResult con success=True y data si fue exitoso,
            o success=False y error si falló.

        Raises:
            ToolExecutionError: Si falla de forma irrecuperable.
        """
        ...

    def validate_args(self, **kwargs) -> bool:
        """Valida que los argumentos sean correctos antes de ejecutar.

        Debe llamarse ANTES de execute() para evitar errores en runtime.

        Args:
            **kwargs: Argumentos a validar.

        Returns:
            True si los argumentos son válidos, False de lo contrario.
        """
        ...
