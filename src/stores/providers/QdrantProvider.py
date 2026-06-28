from typing import List, Optional, Dict, Any
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.models import Distance, VectorParams
from src.stores.vectordb.VectorDB_Interface import BaseVectorDB
from src.stores.vectordb.VectorDB_Enums import DistanceMethodEnums
from src.models.db_schemas.retrieval import RetrievedDocument
from src.models.db_schemas.chunk import RetrievedChunk
import uuid
import logging

logger = logging.getLogger(__name__)

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
        if not self.client:
            await self.connect()
        collections = await self.client.get_collections()
        return [c.name for c in collections.collections]

    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get info about a Qdrant collection."""
        if not self.client:
            await self.connect()
        collection_info = await self.client.get_collection(collection_name=collection_name)
        return collection_info.dict()

    async def delete_collection(self, collection_name: str):
        """Delete a collection from Qdrant."""
        if not self.client:
            await self.connect()
        if await self.is_collection_existed(collection_name):
            await self.client.delete_collection(collection_name=collection_name)

    async def create_collection(self, collection_name: str, 
                                embedding_size: int,
                                do_reset: bool = False,
                                distance_method: str = "cosine"):
        """Create a new collection in Qdrant with specific vector configuration."""
        if not self.client:
            await self.connect()

        if do_reset:
            await self.delete_collection(collection_name)
            
        # Check if collection exists
        if await self.is_collection_existed(collection_name):
            # If it exists, verify the dimension
            info = await self.get_collection_info(collection_name)
            # Qdrant info structure: info['config']['params']['vectors']['size']
            current_dim = info.get('config', {}).get('params', {}).get('vectors', {}).get('size')
            
            if current_dim != embedding_size:
                logger.warning(f"Dimension mismatch for {collection_name}: Found {current_dim}, expected {embedding_size}. Recreating...")
                await self.delete_collection(collection_name)
            else:
                # Dimension matches, no need to recreate
                return

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
        if not self.client:
            await self.connect()
        
        # Combine text and metadata
        payload = metadata if metadata else {}
        payload["text"] = text
        
        await self.client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=record_id or str(uuid.uuid4()),
                    vector=vector,
                    payload=payload
                )
            ]
        )

    async def insert_many(self, collection_name: str, texts: list, 
                          vectors: list, metadata: list = None, 
                          record_ids: list = None, batch_size: int = 50):
        """Insert multiple records into Qdrant."""
        if not self.client:
            await self.connect()
            
        points = []
        for i in range(len(texts)):
            payload = metadata[i] if metadata and i < len(metadata) else {}
            payload["text"] = texts[i]
            
            points.append(
                models.PointStruct(
                    id=record_ids[i] if record_ids and i < len(record_ids) else str(uuid.uuid4()),
                    vector=vectors[i],
                    payload=payload
                )
            )
            
        # Batch upload
        for i in range(0, len(points), batch_size):
            await self.client.upsert(
                collection_name=collection_name,
                points=points[i:i+batch_size]
            )

    async def search_by_vector(self, collection_name: str, vector: list, limit: int) -> Optional[List[RetrievedChunk]]:
        """Search Qdrant using the query_points API."""
        if not self.client:
            await self.connect()
            
        try:
            # Use query_points (modern API)
            response = await self.client.query_points(
                collection_name=collection_name,
                query=vector,
                limit=limit
            )
            search_results = response.points
        except Exception as e:
            # Handle the case where the collection doesn't exist
            logger.error(f"Search failed for collection {collection_name}: {e}")
            return None

        if not search_results or len(search_results) == 0:
            return None

        return [
            RetrievedChunk(
                chunk_uuid=str(res.id),
                file_id=getattr(res, 'payload', {}).get("file_id", ""),
                chunk_text=getattr(res, 'payload', {}).get("text", ""),
                score=getattr(res, 'score', 0.0),
                chunk_metadata=getattr(res, 'payload', {})
            )
            for res in search_results
        ]
