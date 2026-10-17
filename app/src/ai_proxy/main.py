import json
from time import perf_counter, time
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse, StreamingResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field

from .backends import InferenceBackend, MockBackend, OllamaBackend
from .config import get_settings

REQUESTS = Counter("ai_proxy_requests_total", "Inference requests", ["method", "path", "status"])
LATENCY = Histogram("ai_proxy_request_duration_seconds", "Request latency", ["method", "path"])


class InferenceRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8192)


class InferenceResponse(BaseModel):
    response: str
    model: str


class ChatCompletionRequest(BaseModel):
    model: str | None = None
    messages: list[dict[str, Any]] = Field(min_length=1)
    stream: bool = False


def create_backend() -> InferenceBackend:
    settings = get_settings()
    if settings.backend == "ollama":
        return OllamaBackend(settings.ollama_url, settings.ollama_model, settings.request_timeout_seconds)
    return MockBackend()


app = FastAPI(title="AI Inference Proxy", version="0.1.0")
backend = create_backend()


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    started = perf_counter()
    response = await call_next(request)
    path = request.url.path
    REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    LATENCY.labels(request.method, path).observe(perf_counter() - started)
    return response


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
async def readyz() -> dict[str, str]:
    if not await backend.ready():
        raise HTTPException(status_code=503, detail="inference backend is not ready")
    return {"status": "ready"}


@app.get("/v1/models")
async def list_models() -> dict[str, Any]:
    try:
        model_ids = await backend.list_models()
    except Exception as exc:
        raise HTTPException(status_code=502, detail="inference backend model listing failed") from exc
    return {
        "object": "list",
        "data": [
            {"id": model_id, "object": "model", "created": 0, "owned_by": "local"}
            for model_id in model_ids
        ],
    }


@app.post("/v1/chat/completions", response_model=None)
async def chat_completions(payload: ChatCompletionRequest) -> dict[str, Any] | StreamingResponse:
    settings = get_settings()
    model = payload.model or (settings.ollama_model if settings.backend == "ollama" else "mock")
    completion_id = f"chatcmpl-{uuid4().hex}"
    created = int(time())
    if not payload.stream:
        try:
            result = await backend.chat(payload.messages, model)
        except Exception as exc:
            raise HTTPException(status_code=502, detail="inference backend chat request failed") from exc
        return {
            "id": completion_id,
            "object": "chat.completion",
            "created": created,
            "model": result.model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": result.response},
                    "finish_reason": "stop",
                }
            ],
        }

    stream = backend.stream_chat(payload.messages, model)
    try:
        first_content = await anext(stream, None)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="inference backend chat request failed") from exc

    def encode_chunk(delta: dict[str, str], finish_reason: str | None = None) -> str:
        chunk = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
        }
        return f"data: {json.dumps(chunk, separators=(',', ':'))}\n\n"

    async def event_stream():
        yield encode_chunk({"role": "assistant"})
        if first_content:
            yield encode_chunk({"content": first_content})
        try:
            async for content in stream:
                yield encode_chunk({"content": content})
        except Exception as exc:
            error = {"error": {"type": "server_error", "message": str(exc)}}
            yield f"data: {json.dumps(error, separators=(',', ':'))}\n\n"
            yield "data: [DONE]\n\n"
            return
        yield encode_chunk({}, finish_reason="stop")
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/v1/inference", response_model=InferenceResponse)
async def inference(payload: InferenceRequest) -> InferenceResponse:
    try:
        result = await backend.generate(payload.prompt)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="inference backend request failed") from exc
    return InferenceResponse(response=result.response, model=result.model)


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)
