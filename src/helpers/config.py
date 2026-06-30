from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from functools import lru_cache
from pathlib import Path
from typing import List, Set, Optional, Literal
from enum import Enum

# Get the path to 'src' folder where .env is located
BASE_DIR = Path(__file__).resolve().parent.parent

class FileType(str, Enum):
    PDF = "application/pdf"
    TEXT = "text/plain"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

class Settings(BaseSettings):
    """App configuration using Pydantic Settings."""
    
    APP_NAME: str = "Docsly"
    APP_VERSION: str = "0.1"
    LOG_LEVEL: str = "INFO"
    
    # ========================= LLM Config =========================
    GENERATION_BACKEND: Literal["OPENAI", "COHERE", "OLLAMA", "GEMINI"] = "OPENAI"
    EMBEDDING_BACKEND: Literal["OPENAI", "COHERE", "OLLAMA", "GEMINI"] = "OPENAI"

    OPENAI_API_KEY: str = "Add ur key"
    OPENAI_API_URL: str = "" # Added support for custom API URL (e.g. OpenRouter)
    GEMINI_API_KEY: str = "Add ur key"
    COHERE_API_KEY: str = "Add ur key"
    OLLAMA_API_URL: str = "http://localhost:11434"
    
    GENERATION_MODEL_ID: str = "gpt-3.5-turbo-0125"
    EMBEDDING_MODEL_ID: str = "embed-multilingual-light-v3.0"
    EMBEDDING_MODEL_SIZE: int = 384

    INPUT_DAFAULT_MAX_CHARACTERS: int = 1024
    GENERATION_DAFAULT_MAX_TOKENS: int = 200
    GENERATION_DAFAULT_TEMPERATURE: float = 0.1
    
    # ========================= Vector DB Config =========================
    VECTOR_DB_BACKEND: Literal["QDRANT", "PGVECTOR"] = "QDRANT"
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""
    VECTOR_DB_DISTANCE_METHOD: str = "cosine"
    VECTOR_DB_PGVEC_INDEX_THRESHOLD: int = 10000

    # ========================= Template Configs =========================
    PRIMARY_LANG: str = "ar"
    DEFAULT_LANG: str = "en"

    # File upload and processing settings
    FILE_ALLOWED_TYPES: List[str] = [] # Will be loaded from .env
    FILE_MAX_SIZE: int = 10 * 1024 * 1024
    FILE_DEFAULT_CHUNK_SIZE: int = 512 * 1024
    TEXT_SPLITTER_BACKEND: str = "RECURSIVE" # Can be RECURSIVE or NLTK

    # MongoDB settings
    MONGODB_USERNAME: str = "admin"
    MONGODB_PASSWORD: str = "admin"
    MONGODB_URL: str = ""
    MONGODB_DATABASE_NAME: str = ""


    # PostgreSQL + pgvector settings
    POSTGRES_USERNAME: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: int = 5432
    POSTGRES_MAIN_DATABASE: Optional[str] = None

    @model_validator(mode='after')
    def validate_pg_settings(self):
        if self.VECTOR_DB_BACKEND == "PGVECTOR":
            missing = []
            if not self.POSTGRES_USERNAME:
                missing.append("POSTGRES_USERNAME")
            if not self.POSTGRES_PASSWORD:
                missing.append("POSTGRES_PASSWORD")
            if not self.POSTGRES_HOST:
                missing.append("POSTGRES_HOST")
            if not self.POSTGRES_MAIN_DATABASE:
                missing.append("POSTGRES_MAIN_DATABASE")
            if missing:
                raise ValueError(
                    f"PostgreSQL credentials must be provided when VECTOR_DB_BACKEND is PGVECTOR. "
                    f"Missing: {', '.join(missing)}"
                )
        return self

    # Read from .env file
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='ignore'
    )

# Create settings object
@lru_cache
def get_settings():
    """Get app settings. Uses cache for speed."""
    return Settings()
