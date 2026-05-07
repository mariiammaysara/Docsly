from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path
from typing import List, Set
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
    GENERATION_BACKEND: str = "OPENAI"
    EMBEDDING_BACKEND: str = "OPENAI"

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
    VECTOR_DB_BACKEND: str = "QDRANT"
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""
    VECTOR_DB_DISTANCE_METHOD: str = "cosine"
    VECTOR_DB_PGVEC_INDEX_THRESHOLD: int = 10000

    # ========================= Template Configs =========================
    PRIMARY_LANG: str = "ar"
    DEFAULT_LANG: str = "en"

    # File upload settings
    FILE_ALLOWED_TYPES: List[str] = [] # Will be loaded from .env
    FILE_MAX_SIZE: int = 10 * 1024 * 1024
    FILE_DEFAULT_CHUNK_SIZE: int = 512 * 1024

    # MongoDB settings
    MONGODB_USERNAME: str = "admin"
    MONGODB_PASSWORD: str = "admin"
    MONGODB_URL: str
    MONGODB_DATABASE_NAME: str

    
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
