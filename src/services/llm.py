"""LLM service — wrapper sobre OllamaClient para abstraer el proveedor."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.rag.generation.ollama_client import OllamaClient


class LLMServiceError(Exception):
    """Error base para fallos del servicio LLM."""


class LLMTimeoutError(LLMServiceError):
    """Timeout al conectar con el LLM."""

    def __init__(self, model: str, timeout: float) -> None:
        super().__init__(f"Timeout after {timeout}s with model {model}")
        self.model = model
        self.timeout = timeout


class LLMConnectionError(LLMServiceError):
    """No se pudo conectar con el LLM."""

    def __init__(self, url: str, error: Exception) -> None:
        super().__init__(f"Cannot connect to LLM at {url}: {error}")
        self.url = url
        self.original_error = error


class LLMService:
    """Wrapper sobre OllamaClient para abstraer el proveedor LLM.

    Precondiciones: Ollama corriendo en la URL configurada.
    Postcondiciones: Retorna texto generado o levanta LLMError.
    Excepciones: LLMTimeoutError, LLMConnectionError.

    Uso::

        service = LLMService(base_url="http://localhost:11434", model="phi3:mini")
        response = await service.generate("Genera una rutina de ejercicios...")
        health = await service.health_check()
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 600.0,
    ) -> None:
        """Initialize LLM service.

        Args:
            base_url: URL base de Ollama. Default: OLLAMA_URL env var.
            model: Modelo a usar. Default: OLLAMA_MODEL env var.
            timeout: Timeout para llamadas LLM en segundos.
        """
        self._client = OllamaClient(
            base_url=base_url or os.getenv("OLLAMA_URL", "http://localhost:11434"),
            model=model or os.getenv("OLLAMA_MODEL", "phi3:mini"),
            timeout=timeout,
        )
        self.model = self._client.model

    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        format_json: bool = False,
    ) -> str:
        """Send a prompt to Ollama and return the full response text.

        Args:
            prompt: User prompt.
            system: Optional system prompt.
            format_json: Force JSON output format.

        Returns:
            The generated text response.

        Raises:
            LLMTimeoutError: If Ollama times out.
            LLMConnectionError: If cannot connect to Ollama.
        """
        try:
            return await self._client.generate(
                prompt, system=system, format_json=format_json
            )
        except ConnectionError as e:
            raise LLMConnectionError(self._client.base_url, e) from e

    async def generate_stream(
        self, prompt: str, *, system: str | None = None
    ) -> str:
        """Generate with streaming (returns final accumulated text).

        Args:
            prompt: User prompt.
            system: Optional system prompt.

        Returns:
            The full accumulated response text.
        """
        try:
            return await self._client.generate(
                prompt, system=system, stream=True
            )
        except ConnectionError as e:
            raise LLMConnectionError(self._client.base_url, e) from e

    async def health_check(self) -> bool:
        """Return True if Ollama is reachable and the model is available.

        Returns:
            True if healthy, False otherwise.
        """
        return await self._client.health_check()
