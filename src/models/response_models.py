from pydantic import BaseModel

class MessageResponse(BaseModel):
    """Simple model for messages."""
    message: str
    version: str

class HealthResponse(BaseModel):
    """Simple model for health status."""
    status: str
    app: str

class FileUploadResponse(BaseModel):
    """Response model for file upload."""
    message: str
    project_id: str
    file_name: str
    file_size: int

