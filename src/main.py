"""
Docsly - RAG Application
========================
Main app file. 
Sets up FastAPI, loads config, 
and adds routes.
"""

from fastapi import FastAPI, Depends
from routes.base import router as base_router
from routes.data import data_router
from helpers.config import get_settings, Settings
from controllers import base_controller
from models.response_models import MessageResponse
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
import logging

# ---------------------------------------------------------------------------
# Logging Configuration
# Set up a professional format for all project loggers early in the lifecycle
# ---------------------------------------------------------------------------
settings = get_settings()

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App Setup
# Get config for app metadata
# ---------------------------------------------------------------------------
# settings = get_settings() # Moved up to support logging config early

# ---------------------------------------------------------------------------
# App Setup with MongoDB Lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize MongoDB Client
    logger.info("Initializing MongoDB connection...")
    try:
        app.db_client = AsyncIOMotorClient(settings.MONGODB_URL)
        app.db = app.db_client[settings.MONGODB_DATABASE_NAME]
        
        # Ping the database to verify connection
        await app.db.command("ping")
        logger.info("MongoDB connection established successfully.")

        # Enforce Indices and Initialize Collections via Async Factory Method
        from models import ProjectRepository, ChunkRepository, AssetModel
        
        await ProjectRepository.create(app.db)
        await ChunkRepository.create(app.db)
        await AssetModel.create_instance(app.db)
        
        logger.info("Database collections and indices initialized (Factory Pattern).")

        # ---------------------------------------------------------------------------
        # LLM Clients Initialization
        # ---------------------------------------------------------------------------
        from stores.llm import LLMProviderFactory
        llm_factory = LLMProviderFactory(settings)

        # Initialize Generation Client
        app.generation_client = llm_factory.create(settings.GENERATION_BACKEND)
        
        # Initialize Embedding Client
        app.embedding_client = llm_factory.create(settings.EMBEDDING_BACKEND)

        logger.info(f"LLM Clients initialized (Generation: {settings.GENERATION_BACKEND}, Embedding: {settings.EMBEDDING_BACKEND})")

    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise e

    yield

    # Shutdown: Close MongoDB Client
    logger.info("Closing MongoDB connection...")
    app.db_client.close()

app = FastAPI(
    title=settings.APP_NAME,
    description="RAG Application API",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Middleware to fix double slashes in URL
@app.middleware("http")
async def fix_double_slashes(request, call_next):
    path = request.scope.get("path")
    if path and "//" in path:
        # Replace multiple slashes with one
        request.scope["path"] = path.replace("//", "/")
    return await call_next(request)


# ---------------------------------------------------------------------------
# Add Routes
# Keeping main.py clean by using routers
# ---------------------------------------------------------------------------
app.include_router(base_router)
app.include_router(data_router)



# ---------------------------------------------------------------------------
# Home Route
# Logic is in BaseController
# ---------------------------------------------------------------------------
@app.get("/", tags=["root"], response_model=MessageResponse)
async def welcome(settings: Settings = Depends(get_settings)):
    """Welcome message from the controller."""
    return await base_controller.get_welcome_message(settings)
