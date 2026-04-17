from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import uuid
from typing import Optional
from ..base_data_model import PyObjectId

class Project(BaseModel):
    """
    Schema for the 'Project' collection.
    Tracks individual project metadata and discovery.
    """
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    project_id: str = Field(..., description="Unique human-readable project identifier")
    project_uuid: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    processing_status: Optional[str] = Field(default="pending", description="Current processing status of the project")
    
    @classmethod
    def get_indexes(cls):
        """Returns the declarative index specifications for the 'projects' collection."""
        return [
            {
                "key": [("project_id", 1)],
                "name": "project_id_index_1",
                "unique": True
            },
            {
                "key": [("project_uuid", 1)],
                "name": "project_uuid_index_1",
                "unique": True
            }
        ]

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "project_id": "docsly_v1",
                "created_at": "2026-03-04T06:00:00Z",
                "updated_at": "2026-03-04T06:00:00Z"
            }
        }
    )
