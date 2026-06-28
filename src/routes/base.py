from fastapi import APIRouter, Depends
from src.controllers import BaseController
from src.models.response_models import HealthResponse
from src.helpers.config import get_settings, Settings

# Instantiate base controller
base_ctrl = BaseController()

# General routes
router = APIRouter(
    prefix="/api/v1",
    tags=["API v1"],
)

@router.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)):
    """Health check from the controller."""
    return await base_ctrl.get_health_status(settings)
