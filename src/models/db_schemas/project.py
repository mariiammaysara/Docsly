from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import uuid
from typing import Optional, Any
from ..base_data_model import PyObjectId
from ..enums import ProcessingStatusEnum

class Project(BaseModel):
    """
    Schema for the 'Project' collection.
    Tracks individual project metadata and discovery.
    """
    id: Optional[Any] = Field(alias="_id", default=None)
    project_id: str = Field(..., description="Unique human-readable project identifier")
    project_uuid: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True)
    
    project_pushed_at: datetime = Field(default_factory=datetime.utcnow)
    project_updated_at: datetime = Field(default_factory=datetime.utcnow)
    processing_status: ProcessingStatusEnum = Field(default=ProcessingStatusEnum.PENDING, description="Current processing status of the project")
    
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
                "project_pushed_at": "2026-03-04T06:00:00Z",
                "project_updated_at": "2026-03-04T06:00:00Z"
            }
        }
    )
