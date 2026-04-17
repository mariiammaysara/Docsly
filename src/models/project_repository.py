from .base_data_model import BaseDataModel
from .db_schemas import Project
from .enums import DataBaseEnum
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
import logging

logger = logging.getLogger(__name__)

class ProjectRepository(BaseDataModel):
    """
    Repository class for the 'projects' collection.
    Handles data access logic for Project entities.
    """
    def __init__(self, db_client: AsyncIOMotorDatabase):
        super().__init__(db_client=db_client)
        self.collection: AsyncIOMotorCollection = self.db_client[DataBaseEnum.COLLECTION_PROJECT_NAME.value]
        
    @classmethod
    async def create(cls, db_client):
        """Async factory method to create and initialize the repository."""
        instance = cls(db_client)
        await instance.init_collection()
        return instance
        
    async def init_collection(self):
        """Robust initialization of the projects collection and its indexes."""
        all_collections = await self.db_client.list_collection_names()
        if DataBaseEnum.COLLECTION_PROJECT_NAME.value not in all_collections:
            # Re-initialize self.collection just to be safe during first-time creation
            self.collection = self.db_client[DataBaseEnum.COLLECTION_PROJECT_NAME.value]
            indexes = Project.get_indexes()
            for index in indexes:
                await self.collection.create_index(
                    index["key"],
                    name=index["name"],
                    unique=index["unique"]
                )

    async def create_project(self, project: Project):
        """Creates a new project record and returns the instance."""
        try:
            result = await self.collection.insert_one(project.model_dump(by_alias=True, exclude_none=True))
            project.id = result.inserted_id
            return project
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            raise e

    async def get_project_or_create_one(self, project_id: str):
        """
        Retrieves a project by its human-readable ID, 
        or creates a new one atomically using upsert.
        """
        try:
            # Atomic upsert to prevent data duplication under concurrency
            project_data = await self.collection.find_one_and_update(
                {"project_id": project_id},
                {"$setOnInsert": Project(project_id=project_id).model_dump(by_alias=True, exclude_none=True)},
                upsert=True,
                return_document=True
            )
            return Project(**project_data)
        except Exception as e:
            logger.error(f"Error in get_project_or_create_one for {project_id}: {e}")
            raise e

    async def find_one(self, query: dict) -> Optional[Project]:
        """Retrieves a single project matching the query and converts it to a Model."""
        try:
            project_data = await self.collection.find_one(query)
            if project_data:
                return Project(**project_data)
            return None
        except Exception as e:
            logger.error(f"Error in find_one for query {query}: {e}")
            return None

    async def find_all(self, query: Optional[dict] = None) -> List[Project]:
        """Retrieves all projects matching the query and converts them to Models."""
        try:
            query = query or {}
            projects_cursor = self.collection.find(query)
            projects_data = await projects_cursor.to_list(length=None)
            return [Project(**data) for data in projects_data]
        except Exception as e:
            logger.error(f"Error in find_all for query {query}: {e}")
            return []

    async def find_paginated(self, query: Optional[dict] = None, page: int = 1, page_size: int = 10) -> List[Project]:
        """
        Retrieves projects matching the query with pagination support.
        """
        try:
            query = query or {}
            skip = (page - 1) * page_size
            cursor = self.collection.find(query).skip(skip).limit(page_size)
            projects_data = await cursor.to_list(length=page_size)
            return [Project(**data) for data in projects_data]
        except Exception as e:
            logger.error(f"Error in find_paginated for query {query}: {e}")
            return []

