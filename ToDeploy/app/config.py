"""Application settings for Cloud Run / local docker (ToDeploy package)."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# ToDeploy/app/config.py → package root is parents[1]
_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    materials_dir: Path = _ROOT / "data" / "materials"
    plant_dir: Path = _ROOT / "data" / "plant_library"
    embedding_onnx: Path = _ROOT / "data" / "embedding" / "model.onnx"
    embedding_vocab: Path = _ROOT / "data" / "embedding" / "vocab.txt"

    # Optional GGUF (mount or place under models/)
    llm_model_path: Path | None = None
    llm_n_ctx: int = 1024
    llm_n_threads: int = 4
    llm_max_tokens: int = 256
    llm_temperature: float = 0.3

    cors_origins: str = "*"

    host: str = "0.0.0.0"
    port: int = 8080


settings = Settings()
