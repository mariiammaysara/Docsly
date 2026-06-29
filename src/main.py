"""
Docsly - RAG Application
========================
Main app file. 
Sets up FastAPI, loads config, 
and adds routes.
"""

from fastapi import FastAPI, Depends
from src.routes.base import router as base_router
from src.routes.data import data_router
from src.routes.nlp import nlp_router
from src.helpers.config import get_settings, Settings
from src.controllers import BaseController
from src.models.response_models import MessageResponse
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.models.db_schemas.docsly import Base

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
# App Setup with PostgreSQL Lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize PostgreSQL Client
    logger.info("Initializing PostgreSQL connection...")
    try:
        postgres_url = f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DATABASE}"
        app.db_engine = create_async_engine(postgres_url, echo=False)
        app.db = async_sessionmaker(app.db_engine, expire_on_commit=False)
        
        # Verify connection and verify tables exist
        async with app.db_engine.begin() as conn:
            from sqlalchemy import text
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("PostgreSQL connection established and tables/extensions initialized.")

        # Initialize Repositories (Factory Pattern)
        from src.models import ProjectRepository, ChunkRepository, AssetModel
        
        await ProjectRepository.create(app.db)
        await ChunkRepository.create(app.db)
        await AssetModel.create_instance(app.db)
        
        logger.info("Database repositories initialized.")

        # ---------------------------------------------------------------------------
        # LLM Clients Initialization
        # ---------------------------------------------------------------------------
        from src.stores.llm import LLMProviderFactory
        llm_factory = LLMProviderFactory(settings)

        # Initialize Generation Client
        app.generation_client = llm_factory.create(settings.GENERATION_BACKEND)
        
        # Initialize Embedding Client
        app.embedding_client = llm_factory.create(settings.EMBEDDING_BACKEND)

        logger.info(f"LLM Clients initialized (Generation: {settings.GENERATION_BACKEND}, Embedding: {settings.EMBEDDING_BACKEND})")

        # ---------------------------------------------------------------------------
        # Vector DB Initialization
        # ---------------------------------------------------------------------------
        from src.stores.vectordb import VectorDBProviderFactory
        # Pass app.db (the SQL sessionmaker) to the VectorDBProviderFactory
        vectordb_factory = VectorDBProviderFactory(settings, db_client=app.db)
        app.vectordb_client = vectordb_factory.create(settings.VECTOR_DB_BACKEND)
        await app.vectordb_client.connect()
        logger.info(f"VectorDB client initialized ({settings.VECTOR_DB_BACKEND})")

        # ---------------------------------------------------------------------------
        # Template Parser Initialization
        # ---------------------------------------------------------------------------
        from src.stores.llm.templates.template_parser import TemplateParser
        app.template_parser = TemplateParser(
            language=settings.PRIMARY_LANG,
            default_language=settings.DEFAULT_LANG,
        )
        logger.info(f"Template Parser initialized (Lang: {settings.PRIMARY_LANG})")

    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        raise e

    yield

    # Shutdown: Close PostgreSQL and VectorDB Connections
    logger.info("Shutting down resources...")
    
    if hasattr(app, 'vectordb_client'):
        await app.vectordb_client.disconnect()
        logger.info("VectorDB connection closed.")

    if hasattr(app, 'db_engine'):
        await app.db_engine.dispose()
        logger.info("PostgreSQL connection closed.")


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
app.include_router(nlp_router)



# Instantiate base controller
base_ctrl = BaseController()

@app.get("/", tags=["root"], response_model=MessageResponse)
async def welcome(settings: Settings = Depends(get_settings)):
    """Welcome message from the controller."""
    return await base_ctrl.get_welcome_message(settings)
