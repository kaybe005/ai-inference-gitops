from dataclasses import dataclass
from typing import Protocol

import httpx


@dataclass(frozen=True)
class InferenceResult:
    response: str
    model: str


class InferenceBackend(Protocol):
    async def generate(self, prompt: str) -> InferenceResult: ...
    async def ready(self) -> bool: ...


class MockBackend:
    async def generate(self, prompt: str) -> InferenceResult:
        return InferenceResult(response=f"mock response: {prompt}", model="mock")

    async def ready(self) -> bool:
        return True


class OllamaBackend:
    def __init__(self, base_url: str, model: str, timeout: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def generate(self, prompt: str) -> InferenceResult:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            payload = response.json()
        return InferenceResult(response=payload["response"], model=payload.get("model", self.model))

    async def ready(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.is_success
        except httpx.HTTPError:
            return False
