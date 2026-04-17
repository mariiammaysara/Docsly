from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
from ..base_data_model import PyObjectId

class Chunk(BaseModel):
    """
    Schema for the 'Chunk' collection.
    Stores decomposed document fragments for vector retrieval and LLM context.
    """
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    chunk_uuid: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True)
    
    chunk_project_id: PyObjectId = Field(..., description="Reference to the owning project")
    asset_id: Optional[str] = Field(None, description="Reference to the specific asset/file record")
    
    file_id: str = Field(..., description="Original filename or unique file ID")
    chunk_order: int = Field(..., gt=0, description="Position of the chunk within the original file")
    
    chunk_text: str = Field(..., min_length=1, description="The raw text content of the chunk")
    chunk_metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata from the loader")
    
    # Audit timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Placeholder for future vector enrichment
    vector_id: Optional[str] = Field(None, description="External ID for vector database reference")
    
    @classmethod
    def get_indexes(cls):
        """Returns the declarative index specifications for the 'chunks' collection."""
        return [
            {
                "key": [("chunk_project_id", 1)],
                "name": "chunk_project_id_index_1",
                "unique": False
            },
            {
                "key": [("chunk_uuid", 1)],
                "name": "chunk_uuid_index_1",
                "unique": True
            },
            {
                "key": [("asset_id", 1)],
                "name": "asset_id_index_1",
                "unique": False
            }
        ]

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "project_id": "docsly_v1",
                "file_id": "sample.pdf",
                "chunk_index": 0,
                "page_content": "This is a sample chunk content.",
                "metadata": {"source": "sample.pdf", "page": 1}
            }
        }
    )
