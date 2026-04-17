from .base_data_model import BaseDataModel
from .db_schemas.asset import Asset
from .enums import DataBaseEnum
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
import logging

logger = logging.getLogger(__name__)

class AssetRepository(BaseDataModel):
    """
    Repository class for the 'assets' collection.
    Handles data access logic for Asset entities.
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
        """Robust initialization of the assets collection and its indexes."""
        all_collections = await self.db_client.list_collection_names()
        if DataBaseEnum.COLLECTION_ASSET_NAME.value not in all_collections:
            self.collection = self.db_client[DataBaseEnum.COLLECTION_ASSET_NAME.value]
            indexes = Asset.get_indexes()
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

    async def find_all(self, query: Optional[dict] = None) -> List[Asset]:
        """Retrieves all assets matching the query and converts them to Models."""
        try:
            query = query or {}
            cursor = self.collection.find(query)
            data_list = await cursor.to_list(length=None)
            return [Asset(**data) for data in data_list]
        except Exception as e:
            logger.error(f"Error in find_all for query {query}: {e}")
            return []

    async def delete_asset(self, asset_id: str) -> bool:
        """Deletes an asset by its ID."""
        try:
            result = await self.collection.delete_one({"_id": asset_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete asset {asset_id}: {e}")
            return False
