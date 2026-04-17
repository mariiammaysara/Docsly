from fastapi import APIRouter, Depends
from controllers import base_controller
from models.response_models import HealthResponse
from helpers.config import get_settings, Settings

# General routes
router = APIRouter(
    prefix="/api/v1",
    tags=["API v1"],
)

@router.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)):
    """Health check from the controller."""
    return await base_controller.get_health_status(settings)
