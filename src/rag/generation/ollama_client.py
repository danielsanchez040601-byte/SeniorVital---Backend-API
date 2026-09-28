"""Async client for Ollama LLM inference."""

import json
import os
from typing import Any

import httpx


DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "phi3:mini"
DEFAULT_TIMEOUT = 60.0


class OllamaClient:
    """Async HTTP client for Ollama /api/generate.

    Reuses the same call pattern established in routines-ai-service.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = (base_url or os.getenv("OLLAMA_URL", DEFAULT_OLLAMA_URL)).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", DEFAULT_MODEL)
        self.timeout = timeout

    def _build_urls(self) -> list[str]:
        """Return fallback URLs: configured first, then localhost/127.0.0.1 swap."""
        urls = [self.base_url]
        if "localhost" in self.base_url:
            urls.append(self.base_url.replace("localhost", "127.0.0.1"))
        return urls

    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        stream: bool = False,
        num_predict: int = 600,
        temperature: float = 0.2,
        top_p: float = 0.9,
        num_ctx: int = 4096,
        format_json: bool = False,
    ) -> str:
        """Send a prompt to Ollama and return the full response text."""
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "num_predict": num_predict,
                "temperature": temperature,
                "top_p": top_p,
                "num_ctx": num_ctx,
            },
        }
        if system:
            payload["system"] = system
        if format_json:
            payload["format"] = "json"

        last_error: Exception | None = None
        for url in self._build_urls():
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if stream:
                        return await self._stream_response(client, url, payload)
                    return await self._full_response(client, url, payload)
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                last_error = exc
                continue

        raise ConnectionError(
            f"Could not connect to Ollama at {self.base_url}: {last_error}"
        )

    async def _full_response(self, client: httpx.AsyncClient, url: str, payload: dict) -> str:
        resp = await client.post(f"{url}/api/generate", json=payload)
        resp.raise_for_status()
        return resp.json()["response"]

    async def _stream_response(self, client: httpx.AsyncClient, url: str, payload: dict) -> str:
        parts: list[str] = []
        async with client.stream("POST", f"{url}/api/generate", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line:
                    data = json.loads(line)
                    parts.append(data.get("response", ""))
        return "".join(parts)

    async def health_check(self) -> bool:
        """Return True if Ollama is reachable and the model is available."""
        for url in self._build_urls():
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(f"{url}/api/tags")
                    if resp.status_code == 200:
                        models = [m["name"] for m in resp.json().get("models", [])]
                        return any(self.model in m for m in models)
            except (httpx.TimeoutException, httpx.ConnectError):
                continue
        return False
