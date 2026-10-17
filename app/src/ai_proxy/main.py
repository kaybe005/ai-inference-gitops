from time import perf_counter

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
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
