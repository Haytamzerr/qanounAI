"""Central configuration.

Every setting is read from environment variables (or a local `.env` file),
never hard-coded. Secrets such as API keys must never be committed: put them
in `.env`, which is git-ignored, and document their names in `.env.example`.
"""

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="QANOUN_", extra="ignore")

    # Data locations
    data_dir: Path = PROJECT_ROOT / "data"

    # Language used when the question's language can't be detected
    default_language: str = "fr"

    # LLM provider (filled in from Phase 3)
    llm_api_key: SecretStr | None = None
    llm_fast_model: str = ""
    llm_strong_model: str = ""

    # Embedding model: multilingual (Arabic + French), runs locally on the CPU
    embedding_model: str = "BAAI/bge-m3"
    embedding_max_tokens: int = 1024  # longer articles are cut; only 2 of 1,329 exceed it
    embedding_batch_size: int = 8  # small batches keep memory low on an 8 GB laptop

    # Services (filled in from Phase 2)
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "articles"
    redis_url: str = "redis://localhost:6379/0"

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def interim_dir(self) -> Path:
        return self.data_dir / "interim"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def embeddings_dir(self) -> Path:
        return self.processed_dir / "embeddings"


settings = Settings()
