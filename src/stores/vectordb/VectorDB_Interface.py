from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from src.models.db_schemas.retrieval import RetrievedDocument

class BaseVectorDB(ABC):
    """
    Blueprint for any Vector Database provider (Advanced Async Version).
    """
    def __init__(self, config):
        self.config = config

    @abstractmethod
    async def connect(self):
        """Establish connection to the vector database."""
        pass

    @abstractmethod
    async def disconnect(self):
        """Close connection to the vector database."""
        pass

    @abstractmethod
    async def is_collection_existed(self, collection_name: str) -> bool:
        """Check if a collection exists."""
        pass

    @abstractmethod
    async def list_all_collections(self) -> List[str]:
        """List all collection names."""
        pass

    @abstractmethod
    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get detailed information about a collection."""
        pass

    @abstractmethod
    async def delete_collection(self, collection_name: str):
        """Delete a collection from the vector database."""
        pass

    @abstractmethod
    async def create_collection(self, collection_name: str, 
                                embedding_size: int,
                                do_reset: bool = False,
                                distance_method: str = "cosine"):
        """Create a new collection."""
        pass

    @abstractmethod
    async def insert_one(self, collection_name: str, text: str, vector: list,
                         metadata: dict = None, 
                         record_id: str = None):
        """Insert a single record into the collection."""
        pass

    @abstractmethod
    async def insert_many(self, collection_name: str, texts: list, 
                          vectors: list, metadata: list = None, 
                          record_ids: list = None, batch_size: int = 50):
        """Insert multiple records using batching."""
        pass

    @abstractmethod
    async def search_by_vector(self, collection_name: str, vector: list, limit: int) -> List[RetrievedDocument]:
        """Search for the most similar vectors and return standardized results."""
        pass
