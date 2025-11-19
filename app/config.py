"""Configuration file with Env Support"""

import json
import logging
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """Configuration class"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Factory Configuration
    LLM_TYPE: str = "ollama"
    DATABASE_TYPE: str = "redis"
    EXTRACTOR_TYPE: str = "docling"
    CHUNKER_TYPE: str = "docling-hybrid"
    EMBEDDINGS_TYPE: str = "huggingface"
    CACHE_TYPE: str = "redis-cache"

    # Ollama Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"

    # Temp File Configuration
    UPLOAD_DIR: Path = Path(__file__).resolve().parent.parent / "tmp" / "uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt", ".md"]

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"
    COLLECTION_NAME: str = "default"
    DISTANCE_METRIC: str = "cosine"

    # Embeddings Configuration
    MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    CACHE_FOLDER: str = "cache"
    EMBEDDING_DIMENSIONS: int = 384

    # Chunk Configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    SEPARATORS: List[str] = [
        "\n\n",
        "\n",
        " ",
        ".",
        ",",
        "\u200b",
        "\uff0c",
        "\u3001",
        "\uff0e",
        "\u3002",
        "",
    ]

    # Server Configuration
    BACKEND_URL: str = "http://localhost:8000"
    CORS_ORIGINS: str | List[str] = ["http://localhost:8501", "http://127.0.0.1:8000/"]

    # RAG Configuration
    RAG_ENABLED: bool = True
    RAG_TOP_K: int = 5
    RAG_MIN_SCORE: float = 0.7

    # Performance Configuration
    ENABLE_CACHING: bool = True
    CACHE_TTL: int = 3600

    # Redis Key Patterns Configuration
    CACHE_KEY_PREFIX: str = "cache:"
    CACHE_DOC_STATE_PATTERN: str = "doc_state:{file_hash}"  # Processing state cache key
    CACHE_DOC_PROCESSING_PATTERN: str = "doc_processing:{file_hash}:{stage}"  # Processing stage cache key
    
    REDIS_DOC_KEY_PREFIX: str = "doc:"
    REDIS_DOC_KEY_PATTERN: str = "doc:*"

    # MinIO Configuration
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "artifacts"
    MINIO_SECURE: bool = False

    # Logging Configuration
    LOG_LEVEL: int = logging.DEBUG  # Can be set via env as: DEBUG, INFO, WARNING, ERROR, CRITICAL

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def parse_log_level(cls, v):
        """Parse LOG_LEVEL from string to logging level integer"""

        if isinstance(v, int):
            return v
        
        if isinstance(v, str):
            level_name = v.upper().strip()
            level_map = {
                "DEBUG": logging.DEBUG,
                "INFO": logging.INFO,
                "WARNING": logging.WARNING,
                "ERROR": logging.ERROR,
                "CRITICAL": logging.CRITICAL,
            }
            if level_name in level_map:
                return level_map[level_name]
                
            return logging.DEBUG
        
        return logging.DEBUG

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS env"""

        if isinstance(v, str):
            s = v.strip()
            if not s:
                return ["http://localhost:8501", "http://127.0.0.1:8000/"]
            try:
                return json.loads(s)

            except (json.JSONDecodeError, ValueError):
                return [origin.strip() for origin in s.split(",") if origin.strip()]

        return v

    @field_validator("UPLOAD_DIR")
    @classmethod
    def create_upload_dir(cls, v: Path) -> Path:
        """Ensure uplaod directory exists"""

        v.mkdir(parents=True, exist_ok=True)
        return v

    def to_dict(self) -> dict:
        """Convert settings to dictionary"""

        return self.model_dump()


config = Settings()
