from typing import Annotated, Any
from pydantic import BeforeValidator, PlainSerializer
from bson import ObjectId
from src.helpers.config import get_settings
from motor.motor_asyncio import AsyncIOMotorDatabase

# ---------------------------------------------------------------------------
# PyObjectId Type Definition (Pydantic v2)
# Handles validation of strings/ObjectIds and serialization to string.
# ---------------------------------------------------------------------------
def validate_object_id(v: Any) -> ObjectId:
    if isinstance(v, ObjectId):
        return v
    if ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError(f"Invalid ObjectId: {v}")

PyObjectId = Annotated[
    ObjectId,
    BeforeValidator(validate_object_id),
    PlainSerializer(lambda v: str(v), return_type=str)
]

class BaseDataModel:
    """
    Base class for all database-interfacing models (Repositories).
    Encapsulates the MongoDB database object with strong typing.
    """
    def __init__(self, db_client: AsyncIOMotorDatabase):
        self.db_client = db_client
        self.app_settings = get_settings()
