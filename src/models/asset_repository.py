from typing import List, Optional, Any
from .base_data_model import BaseDataModel
from .db_schemas.asset import Asset
from .enums import DataBaseEnum
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class AssetModel(BaseDataModel):
    """
    Repository class for the 'assets' collection.
    Handles data access logic for Asset entities.
    """
    def __init__(self, db_client: AsyncIOMotorDatabase):
        super().__init__(db_client=db_client)
        self.collection: AsyncIOMotorCollection = self.db_client[DataBaseEnum.COLLECTION_ASSET_NAME.value]

    @classmethod
    async def create_instance(cls, db_client):
        """Async factory method to create and initialize the repository."""
        instance = cls(db_client)
        await instance.init_collection()
        return instance
    async def init_collection(self):
        """Robust initialization of the assets collection and its indexes."""
        all_collections = await self.db_client.list_collection_names()
        if DataBaseEnum.COLLECTION_ASSET_NAME.value not in all_collections:
            indexes = Asset.get_indexes() # Corrected typo: using Asset instead of Project
            for index in indexes:
                await self.collection.create_index(
                    index["key"],
                    name=index["name"],
                    unique=index["unique"]
                )

    async def create_asset(self, asset: Asset) -> Asset:
        """Creates a new asset record and returns the instance."""
        try:
            result = await self.collection.insert_one(asset.model_dump(by_alias=True, exclude_none=True))
            asset.id = result.inserted_id
            return asset
        except Exception as e:
            logger.error(f"Failed to create asset: {e}")
            raise e

    async def find_one(self, query: dict) -> Optional[Asset]:
        """Retrieves a single asset matching the query and converts it to a Model."""
        try:
            asset_data = await self.collection.find_one(query)
            if asset_data:
                return Asset(**asset_data)
            return None
        except Exception as e:
            logger.error(f"Error in find_one for query {query}: {e}")
            return None

    async def get_all_project_assets(self, asset_project_id: Any, asset_type: str):
        """Retrieves all assets for a specific project and type."""
        try:
            query = {
                "asset_project_id": asset_project_id if isinstance(asset_project_id, ObjectId) else ObjectId(asset_project_id),
                "asset_type": asset_type
            }
            cursor = self.collection.find(query)
            data_list = await cursor.to_list(length=None)
            return [Asset(**data) for data in data_list]
        except Exception as e:
            logger.error(f"Error in get_all_project_assets: {e}")
            return []

    async def get_project_assets(self, asset_project_id: Any):
        """Retrieves all assets (any type) associated with a specific project."""
        try:
            query = {"asset_project_id": asset_project_id if isinstance(asset_project_id, ObjectId) else ObjectId(asset_project_id)}
            cursor = self.collection.find(query)
            data_list = await cursor.to_list(length=None)
            return [Asset(**data) for data in data_list]
        except Exception as e:
            logger.error(f"Error in get_project_assets for {asset_project_id}: {e}")
            return []

    async def get_asset_record(self, asset_project_id: Any, asset_name: str):
        """Retrieves a specific asset by project and name."""
        try:
            query = {
                "asset_project_id": asset_project_id if isinstance(asset_project_id, ObjectId) else ObjectId(asset_project_id),
                "asset_name": asset_name
            }
            asset_data = await self.collection.find_one(query)
            if asset_data:
                return Asset(**asset_data)
            return None
        except Exception as e:
            logger.error(f"Error in get_asset_record: {e}")
            return None

    async def delete_asset(self, asset_id: Any) -> bool:
        """Deletes an asset by its ID."""
        try:
            query_id = asset_id if isinstance(asset_id, ObjectId) else ObjectId(asset_id)
            result = await self.collection.delete_one({"_id": query_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete asset {asset_id}: {e}")
            return False
