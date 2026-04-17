from .base_data_model import BaseDataModel
from .db_schemas import Chunk
from .enums import DataBaseEnum
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
import logging

logger = logging.getLogger(__name__)

class ChunkRepository(BaseDataModel):
    """
    Repository class for the 'chunks' collection.
    Handles data access logic for Chunk entities.
    """
    def __init__(self, db_client: AsyncIOMotorDatabase):
        super().__init__(db_client=db_client)

    @classmethod
    async def create(cls, db_client):
        """Async factory method to create and initialize the repository."""
        instance = cls(db_client)
        await instance.init_collection()
        return instance
    async def init_collection(self):
        """Robust initialization of the chunks collection and its indexes."""
        all_collections = await self.db_client.list_collection_names()
        if DataBaseEnum.COLLECTION_CHUNK_NAME.value not in all_collections:
            self.collection = self.db_client[DataBaseEnum.COLLECTION_CHUNK_NAME.value]
            indexes = Chunk.get_indexes()
            for index in indexes:
                await self.collection.create_index(
                    index["key"],
                    name=index["name"],
                    unique=index["unique"]
                )

    async def insert_many_chunks(self, chunks: List[Chunk]) -> bool:
        """
        Inserts a list of chunk documents into the collection.
        """
        try:
            if not chunks:
                return False
                
            chunk_dicts = [
                chunk.model_dump(by_alias=True, exclude_none=True) 
                for chunk in chunks
            ]
            
            result = await self.collection.insert_many(chunk_dicts)
            return result.acknowledged
        except Exception as e:
            logger.error(f"Failed to insert chunks: {e}")
            return False

    async def find_one(self, query: dict) -> Optional[Chunk]:
        """Retrieves a single chunk matching the query and converts it to a Model."""
        try:
            chunk_data = await self.collection.find_one(query)
            if chunk_data:
                return Chunk(**chunk_data)
            return None
        except Exception as e:
            logger.error(f"Error in find_one for query {query}: {e}")
            return None

    async def find_all(self, query: Optional[dict] = None) -> List[Chunk]:
        """Retrieves all chunks matching the query and converts them to Models."""
        try:
            query = query or {}
            chunks_cursor = self.collection.find(query)
            chunks_data = await chunks_cursor.to_list(length=None)
            return [Chunk(**data) for data in chunks_data]
        except Exception as e:
            logger.error(f"Error in find_all for query {query}: {e}")
            return []

    async def find_paginated(self, query: Optional[dict] = None, page: int = 1, page_size: int = 10) -> List[Chunk]:
        """
        Retrieves chunks matching the query with pagination support.
        """
        try:
            query = query or {}
            skip = (page - 1) * page_size
            cursor = self.collection.find(query).skip(skip).limit(page_size)
            chunks_data = await cursor.to_list(length=page_size)
            return [Chunk(**data) for data in chunks_data]
        except Exception as e:
            logger.error(f"Error in find_paginated for query {query}: {e}")
            return []

    async def get_project_chunks(self, project_id: str) -> List[Chunk]:
        """Retrieves all chunks for a specific project using the generic find_all."""
        return await self.find_all({"chunk_project_id": project_id})

    async def delete_project_chunks(self, project_id: str) -> int:
        """Deletes all chunks associated with a project. Returns the count."""
        try:
            result = await self.collection.delete_many({"chunk_project_id": project_id})
            return result.deleted_count
        except Exception as e:
            logger.error(f"Failed to delete chunks for project {project_id}: {e}")
            return 0

