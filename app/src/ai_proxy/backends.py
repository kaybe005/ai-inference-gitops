from dataclasses import dataclass
import json
from collections.abc import AsyncIterator
from typing import Any, Protocol

import httpx


@dataclass(frozen=True)
class InferenceResult:
    response: str
    model: str


class InferenceBackend(Protocol):
    async def generate(self, prompt: str) -> InferenceResult: ...
    async def chat(self, messages: list[dict[str, Any]], model: str) -> InferenceResult: ...
    def stream_chat(self, messages: list[dict[str, Any]], model: str) -> AsyncIterator[str]: ...
    async def list_models(self) -> list[str]: ...
    async def ready(self) -> bool: ...


class MockBackend:
    async def generate(self, prompt: str) -> InferenceResult:
        return InferenceResult(response=f"mock response: {prompt}", model="mock")

    async def chat(self, messages: list[dict[str, Any]], model: str) -> InferenceResult:
        prompt = str(messages[-1].get("content", "")) if messages else ""
        return InferenceResult(response=f"mock response: {prompt}", model="mock")

    async def stream_chat(self, messages: list[dict[str, Any]], model: str) -> AsyncIterator[str]:
        result = await self.chat(messages, model)
        yield result.response

    async def list_models(self) -> list[str]:
        return ["mock"]

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

    async def chat(self, messages: list[dict[str, Any]], model: str) -> InferenceResult:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={"model": model, "messages": messages, "stream": False},
            )
            response.raise_for_status()
            payload = response.json()
        message = payload.get("message", {})
        return InferenceResult(
            response=message.get("content", ""),
            model=payload.get("model", model),
        )

    async def stream_chat(self, messages: list[dict[str, Any]], model: str) -> AsyncIterator[str]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={"model": model, "messages": messages, "stream": True},
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    payload = json.loads(line)
                    content = payload.get("message", {}).get("content")
                    if content:
                        yield content

    async def list_models(self) -> list[str]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            payload = response.json()
        return [
            name
            for item in payload.get("models", [])
            if (name := item.get("name") or item.get("model"))
        ]

    async def ready(self) -> bool:
        try:
            return bool(await self.list_models())
        except httpx.HTTPError:
            return False
