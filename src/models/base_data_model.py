from typing import Annotated, Any, Union
from src.helpers.config import get_settings
from sqlalchemy.ext.asyncio import async_sessionmaker

# ---------------------------------------------------------------------------
# PyObjectId Type Definition (Pydantic v2 Compatible)
# Redefined to allow int/str IDs for PostgreSQL.
# ---------------------------------------------------------------------------
PyObjectId = Union[int, str]

class BaseDataModel:
    """
    Base class for all database-interfacing models (Repositories).
    Encapsulates the SQLAlchemy session maker with strong typing.
    """
    def __init__(self, db_client: async_sessionmaker):
        self.db_client = db_client
        self.app_settings = get_settings()

