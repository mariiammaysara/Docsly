from typing import List, Optional, Dict, Any
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.models import Distance, VectorParams
from src.stores.vectordb.VectorDB_Interface import BaseVectorDB
from src.stores.vectordb.VectorDB_Enums import DistanceMethodEnums
from src.models.db_schemas.retrieval import RetrievedDocument

class QdrantProvider(BaseVectorDB):
    """
    Implementation of VectorDBInterface for Qdrant.
    """
    def __init__(self, config):
        super().__init__(config)
        self.client = None

    async def connect(self):
        """Establish connection to Qdrant using AsyncQdrantClient."""
        if not self.client:
            url = getattr(self.config, 'QDRANT_URL', "http://localhost:6333")
            api_key = getattr(self.config, 'QDRANT_API_KEY', None)
            
            self.client = AsyncQdrantClient(url=url, api_key=api_key)

    async def disconnect(self):
        """Close connection to Qdrant."""
        if self.client:
            await self.client.close()
            self.client = None

    async def is_collection_existed(self, collection_name: str) -> bool:
        """Check if a collection exists in Qdrant."""
        if not self.client:
            await self.connect()
            
        collections = await self.client.get_collections()
        return any(c.name == collection_name for c in collections.collections)

    async def list_all_collections(self) -> List[str]:
        """List all collections in Qdrant."""
        # TODO: Implement listing
        return []

    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get info about a Qdrant collection."""
        # TODO: Implement info retrieval
        return {}

    async def delete_collection(self, collection_name: str):
        """Delete a collection from Qdrant."""
        # TODO: Implement deletion
        pass

    async def create_collection(self, collection_name: str, 
                                embedding_size: int,
                                do_reset: bool = False,
                                distance_method: str = "cosine"):
        """Create a new collection in Qdrant with specific vector configuration."""
        if not self.client:
            await self.connect()

        if do_reset:
            await self.delete_collection(collection_name)
            
        if not await self.is_collection_existed(collection_name):
            # Map distance method string to Qdrant Distance enum
            distance = Distance.COSINE
            if distance_method == DistanceMethodEnums.EUCLIDEAN.value:
                distance = Distance.EUCLID
            elif distance_method == DistanceMethodEnums.DOT.value:
                distance = Distance.DOT

            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=embedding_size, distance=distance)
            )

    async def insert_one(self, collection_name: str, text: str, vector: list,
                         metadata: dict = None, 
                         record_id: str = None):
        """Insert one record into Qdrant."""
        # TODO: Implement insertion
        pass

    async def insert_many(self, collection_name: str, texts: list, 
                          vectors: list, metadata: list = None, 
                          record_ids: list = None, batch_size: int = 50):
        """Insert multiple records into Qdrant."""
        # TODO: Implement batch insertion
        pass

    async def search_by_vector(self, collection_name: str, vector: list, limit: int) -> List[RetrievedDocument]:
        """Search Qdrant and return results as RetrievedDocument."""
        # TODO: Implement search
        return []
