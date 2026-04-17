from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
from ..base_data_model import PyObjectId

class Asset(BaseModel):
    """
    Schema for the 'Asset' collection.
    Tracks individual file uploads and their metadata.
    """
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    asset_uuid: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True)
    
    project_id: PyObjectId = Field(..., description="Reference to the project this asset belongs to")
    
    asset_name: str = Field(..., description="Original name of the file")
    asset_type: str = Field(..., description="MIME type or category (from AssetTypeEnum)")
    asset_size: int = Field(..., gt=0, description="File size in bytes")
    asset_path: str = Field(..., description="Local or remote path to the binary file")
    
    asset_config: Dict[str, Any] = Field(default_factory=dict, description="Extraction settings (chunk size, etc.)")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @classmethod
    def get_indexes(cls):
        """Returns the declarative index specifications for the 'assets' collection."""
        return [
            {
                "key": [("project_id", 1)],
                "name": "project_id_index_1",
                "unique": False
            },
            {
                "key": [("asset_uuid", 1)],
                "name": "asset_uuid_index_1",
                "unique": True
            }
        ]

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
