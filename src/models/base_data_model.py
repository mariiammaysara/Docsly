from typing import Annotated
from pydantic import BeforeValidator
from helpers.config import get_settings
from motor.motor_asyncio import AsyncIOMotorDatabase

# Custom type for handling MongoDB ObjectIDs in Pydantic v2
PyObjectId = Annotated[str, BeforeValidator(str)]

class BaseDataModel:
    """
    Base class for all database-interfacing models (Repositories).
    Encapsulates the MongoDB database object with strong typing.
    """
    def __init__(self, db_client: AsyncIOMotorDatabase):
        self.db_client = db_client
        self.app_settings = get_settings()
