from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AI_PROXY_", case_sensitive=False)

    backend: Literal["mock", "ollama"] = "mock"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:latest"
    request_timeout_seconds: float = 300.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
