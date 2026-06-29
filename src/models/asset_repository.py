from typing import List, Optional, Any
from .base_data_model import BaseDataModel
from .db_schemas.asset import Asset
from .db_schemas.docsly import PGAsset, PGProject
from sqlalchemy import select
import logging
import uuid

logger = logging.getLogger(__name__)

def _is_valid_uuid(val: Any) -> bool:
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, TypeError):
        return False

class AssetModel(BaseDataModel):
    """
    Repository class for the 'assets' table in PostgreSQL.
    Handles data access logic for Asset entities.
    """
    def __init__(self, db_client):
        super().__init__(db_client=db_client)

    @classmethod
    async def create_instance(cls, db_client):
        """Async factory method to create and initialize the repository."""
        instance = cls(db_client)
        return instance

    async def create_asset(self, asset: Asset) -> Asset:
        """Creates a new asset record and returns the instance."""
        try:
            async with self.db_client() as session:
                async with session.begin():
                    db_asset = PGAsset(
                        asset_uuid=asset.asset_uuid,
                        asset_project_id=int(asset.asset_project_id),
                        asset_name=asset.asset_name,
                        asset_type=asset.asset_type,
                        asset_size=asset.asset_size,
                        asset_path=asset.asset_path,
                        asset_config=asset.asset_config,
                        asset_pushed_at=asset.asset_pushed_at,
                        updated_at=asset.updated_at
                    )
                    session.add(db_asset)
                    await session.flush()
                    asset.id = db_asset.id
                    return asset
        except Exception as e:
            logger.error(f"Failed to create asset: {e}")
            raise e

    async def find_one(self, query: dict) -> Optional[Asset]:
        """Retrieves a single asset matching the query and converts it to a Model."""
        try:
            async with self.db_client() as session:
                stmt = select(PGAsset)
                if "asset_uuid" in query:
                    stmt = stmt.where(PGAsset.asset_uuid == query["asset_uuid"])
                elif "asset_name" in query:
                    stmt = stmt.where(PGAsset.asset_name == query["asset_name"])
                elif "asset_project_id" in query:
                    try:
                        project_id_int = int(query["asset_project_id"])
                        stmt = stmt.where(PGAsset.asset_project_id == project_id_int)
                    except (ValueError, TypeError):
                        project_id_val = query["asset_project_id"]
                        if _is_valid_uuid(project_id_val):
                            cond = (PGProject.project_id == project_id_val) | (PGProject.project_uuid == project_id_val)
                        else:
                            cond = (PGProject.project_id == project_id_val)
                        stmt = stmt.join(PGProject).where(cond)
                elif "id" in query:
                    stmt = stmt.where(PGAsset.id == int(query["id"]))
                elif "_id" in query:
                    stmt = stmt.where(PGAsset.id == int(query["_id"]))

                result = await session.execute(stmt)
                db_asset = result.scalars().first()
                if db_asset:
                    return Asset(
                        id=db_asset.id,
                        asset_uuid=str(db_asset.asset_uuid),
                        asset_project_id=db_asset.asset_project_id,
                        asset_name=db_asset.asset_name,
                        asset_type=db_asset.asset_type,
                        asset_size=db_asset.asset_size,
                        asset_path=db_asset.asset_path,
                        asset_config=db_asset.asset_config,
                        asset_pushed_at=db_asset.asset_pushed_at,
                        updated_at=db_asset.updated_at
                    )
                return None
        except Exception as e:
            logger.error(f"Error in find_one for query {query}: {e}")
            return None

    async def get_all_project_assets(self, asset_project_id: Any, asset_type: str):
        """Retrieves all assets for a specific project and type."""
        try:
            async with self.db_client() as session:
                try:
                    project_id_int = int(asset_project_id)
                    stmt = select(PGAsset).where(
                        (PGAsset.asset_project_id == project_id_int) & 
                        (PGAsset.asset_type == asset_type)
                    )
                except (ValueError, TypeError):
                    if _is_valid_uuid(asset_project_id):
                        cond = (PGProject.project_id == asset_project_id) | (PGProject.project_uuid == asset_project_id)
                    else:
                        cond = (PGProject.project_id == asset_project_id)
                    stmt = select(PGAsset).join(PGProject).where(
                        cond & (PGAsset.asset_type == asset_type)
                    )
                result = await session.execute(stmt)
                return [
                    Asset(
                        id=db_asset.id,
                        asset_uuid=str(db_asset.asset_uuid),
                        asset_project_id=db_asset.asset_project_id,
                        asset_name=db_asset.asset_name,
                        asset_type=db_asset.asset_type,
                        asset_size=db_asset.asset_size,
                        asset_path=db_asset.asset_path,
                        asset_config=db_asset.asset_config,
                        asset_pushed_at=db_asset.asset_pushed_at,
                        updated_at=db_asset.updated_at
                    )
                    for db_asset in db_assets
                ]
        except Exception as e:
            logger.error(f"Error in get_all_project_assets: {e}")
            return []

    async def get_project_assets(self, asset_project_id: Any):
        """Retrieves all assets (any type) associated with a specific project."""
        try:
            async with self.db_client() as session:
                try:
                    project_id_int = int(asset_project_id)
                    stmt = select(PGAsset).where(PGAsset.asset_project_id == project_id_int)
                except (ValueError, TypeError):
                    if _is_valid_uuid(asset_project_id):
                        cond = (PGProject.project_id == asset_project_id) | (PGProject.project_uuid == asset_project_id)
                    else:
                        cond = (PGProject.project_id == asset_project_id)
                    stmt = select(PGAsset).join(PGProject).where(cond)
                result = await session.execute(stmt)
                db_assets = result.scalars().all()
                return [
                    Asset(
                        id=db_asset.id,
                        asset_uuid=str(db_asset.asset_uuid),
                        asset_project_id=db_asset.asset_project_id,
                        asset_name=db_asset.asset_name,
                        asset_type=db_asset.asset_type,
                        asset_size=db_asset.asset_size,
                        asset_path=db_asset.asset_path,
                        asset_config=db_asset.asset_config,
                        asset_pushed_at=db_asset.asset_pushed_at,
                        updated_at=db_asset.updated_at
                    )
                    for db_asset in db_assets
                ]
        except Exception as e:
            logger.error(f"Error in get_project_assets for {asset_project_id}: {e}")
            return []

    async def get_asset_record(self, asset_project_id: Any, asset_name: str):
        """Retrieves a specific asset by project and name."""
        try:
            async with self.db_client() as session:
                try:
                    project_id_int = int(asset_project_id)
                    stmt = select(PGAsset).where(
                        (PGAsset.asset_project_id == project_id_int) & 
                        (PGAsset.asset_name == asset_name)
                    )
                except (ValueError, TypeError):
                    if _is_valid_uuid(asset_project_id):
                        cond = (PGProject.project_id == asset_project_id) | (PGProject.project_uuid == asset_project_id)
                    else:
                        cond = (PGProject.project_id == asset_project_id)
                    stmt = select(PGAsset).join(PGProject).where(
                        cond & (PGAsset.asset_name == asset_name)
                    )
                result = await session.execute(stmt)
                db_asset = result.scalars().first()
                if db_asset:
                    return Asset(
                        id=db_asset.id,
                        asset_uuid=str(db_asset.asset_uuid),
                        asset_project_id=db_asset.asset_project_id,
                        asset_name=db_asset.asset_name,
                        asset_type=db_asset.asset_type,
                        asset_size=db_asset.asset_size,
                        asset_path=db_asset.asset_path,
                        asset_config=db_asset.asset_config,
                        asset_pushed_at=db_asset.asset_pushed_at,
                        updated_at=db_asset.updated_at
                    )
                return None
        except Exception as e:
            logger.error(f"Error in get_asset_record: {e}")
            return None

    async def delete_asset(self, asset_id: Any) -> bool:
        """Deletes an asset by its ID."""
        try:
            async with self.db_client() as session:
                async with session.begin():
                    stmt = select(PGAsset).where(PGAsset.id == int(asset_id))
                    result = await session.execute(stmt)
                    db_asset = result.scalars().first()
                    if db_asset:
                        await session.delete(db_asset)
                        return True
                    return False
        except Exception as e:
            logger.error(f"Failed to delete asset {asset_id}: {e}")
            return False

    async def find_paginated(self, query: Optional[dict] = None, page: int = 1, page_size: int = 10) -> List[Asset]:
        """Retrieves assets matching the query with pagination support."""
        try:
            query = query or {}
            skip = (page - 1) * page_size
            async with self.db_client() as session:
                stmt = select(PGAsset)
                if "asset_project_id" in query:
                    try:
                        project_id_int = int(query["asset_project_id"])
                        stmt = stmt.where(PGAsset.asset_project_id == project_id_int)
                    except (ValueError, TypeError):
                        project_id_val = query["asset_project_id"]
                        if _is_valid_uuid(project_id_val):
                            cond = (PGProject.project_id == project_id_val) | (PGProject.project_uuid == project_id_val)
                        else:
                            cond = (PGProject.project_id == project_id_val)
                        stmt = select(PGAsset).join(PGProject).where(cond)
                elif "id" in query:
                    stmt = stmt.where(PGAsset.id == int(query["id"]))
                
                stmt = stmt.offset(skip).limit(page_size)
                result = await session.execute(stmt)
                db_assets = result.scalars().all()
                return [
                    Asset(
                        id=db_asset.id,
                        asset_uuid=str(db_asset.asset_uuid),
                        asset_project_id=db_asset.asset_project_id,
                        asset_name=db_asset.asset_name,
                        asset_type=db_asset.asset_type,
                        asset_size=db_asset.asset_size,
                        asset_path=db_asset.asset_path,
                        asset_config=db_asset.asset_config,
                        asset_pushed_at=db_asset.asset_pushed_at,
                        updated_at=db_asset.updated_at
                    )
                    for db_asset in db_assets
                ]
        except Exception as e:
            logger.error(f"Error in find_paginated for query {query}: {e}")
            return []

