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
    APP_VRESION: str = "0.1" # Using current key name from .env
    OPENAI_API_KEY: str = "Add ur key"
    LOG_LEVEL: str = "INFO"
    
    # File upload settings
    FILE_ALLOWED_TYPES: List[FileType] = [
        FileType.PDF, 
        FileType.TEXT, 
        FileType.DOCX
    ]
    FILE_MAX_SIZE: int = 10 * 1024 * 1024 # 10MB in bytes
    FILE_DEFAULT_CHUNK_SIZE: int = 512 * 1024 # 512KB in bytes

    # MongoDB settings
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
