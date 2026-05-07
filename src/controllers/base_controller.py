from fastapi import UploadFile, HTTPException
from helpers.config import Settings
from models.response_models import MessageResponse, HealthResponse
import random
import string
from pathlib import Path

class BaseController:
    """Controller for general API tasks."""
    
    def generate_random_string(self, length: int = 12) -> str:
        """Generate a secure random string for filenames."""
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))
        
    @staticmethod
    async def get_welcome_message(settings: Settings) -> MessageResponse:
        """Logic for the welcome page."""
        return MessageResponse(
            message=f"Welcome to {settings.APP_NAME} API!",
            version=settings.APP_VERSION
        )
    
    @staticmethod
    async def get_health_status(settings: Settings) -> HealthResponse:
        """Logic for the health check."""
        return HealthResponse(
            status="ok",
            app=settings.APP_NAME
        )

    @staticmethod
    def validate_file(file: UploadFile, settings: Settings) -> int:
        """Validate file size and MIME type. Returns file size."""
        
        # 1. Check MIME Type (Using the renamed variable)
        if file.content_type not in settings.FILE_ALLOWED_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file.content_type} not allowed."
            )
            
        # 2. Check Size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > settings.FILE_MAX_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too big. Max: {settings.FILE_MAX_SIZE / (1024*1024)}MB"
            )
            
        return file_size

# Create controller object
base_controller = BaseController()
