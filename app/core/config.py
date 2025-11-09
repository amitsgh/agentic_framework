"""Configuration File"""

from pathlib import Path

class Configuration:
    """Configuration class"""

    # Factory Configuration
    LLM_TYPE = "ollama"
    DATABASE_TYPE = "redis"
    EXTRACTOR_TYPE = "docling"
    CHUNKER_TYPER = "docling-hybrid"
    EMBEDDINGS_TYPE = "huggingface"

    # Ollama Configuration
    OLLAMA_BASE_URL = ""
    OLLAMA_MODEL = "gpt20b"

    # Temp File Configuration
    UPLOAD_DIR = Path(__file__).resolve().parent.parent / "tmp" / "uploads"

    # Redis Configuration
    REDIS_URL = "redis://localhost:6379"
    COLLECTION_NAME = "default"
    DISTANCE_METRIC = "cosine"

    # Embeddings Configuration
    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    CACHE_FOLDER = "cache"
    EMBEDDING_DIMENSIONS = 384

    # Chunk Configuration
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    SEPARATORS = [
        "\n\n",
        "\n",
        " ",
        ".",
        ",",
        "\u200b",  # Zero-width space
        "\uff0c",  # Fullwidth comma
        "\u3001",  # Ideographic comma
        "\uff0e",  # Fullwidth full stop
        "\u3002",  # Ideographic full stop
        "",
    ]

    # Server Configuation
    BACKEND_URL = "http://localhost:8000"

    def to_dict(self):
        pass


config = Configuration()
