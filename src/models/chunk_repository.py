from typing import List, Optional, Any
from .base_data_model import BaseDataModel
from .db_schemas import Chunk
from .db_schemas.docsly import PGChunk, PGProject
from sqlalchemy import select, func, delete
import logging
import uuid

logger = logging.getLogger(__name__)

def _is_valid_uuid(val: Any) -> bool:
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, TypeError):
        return False

class ChunkRepository(BaseDataModel):
    """
    Repository class for the 'chunks' table in PostgreSQL.
    Handles data access logic for Chunk entities.
    """
    def __init__(self, db_client):
        super().__init__(db_client=db_client)

    @classmethod
    async def create(cls, db_client):
        """Async factory method to create and initialize the repository."""
        instance = cls(db_client)
        return instance

    async def insert_many_chunks(self, chunks: List[Chunk]) -> bool:
        """
        Inserts a list of chunk documents into the PostgreSQL table.
        """
        try:
            if not chunks:
                return False
                
            async with self.db_client() as session:
                async with session.begin():
                    db_chunks = [
                        PGChunk(
                            chunk_uuid=chunk.chunk_uuid,
                            chunk_project_id=int(chunk.chunk_project_id),
                            chunk_asset_id=int(chunk.chunk_asset_id) if chunk.chunk_asset_id else None,
                            file_id=chunk.file_id,
                            chunk_order=chunk.chunk_order,
                            chunk_text=chunk.chunk_text,
                            chunk_metadata=chunk.chunk_metadata,
                            chunk_created_at=chunk.chunk_created_at,
                            chunk_updated_at=chunk.chunk_updated_at,
                            vector_id=chunk.vector_id
                        )
                        for chunk in chunks
                    ]
                    session.add_all(db_chunks)
                    await session.flush()
                    
                    # Map the returned integer database IDs back to the Pydantic chunks
                    for chunk, db_chunk in zip(chunks, db_chunks):
                        chunk.id = db_chunk.id
                    return True
        except Exception as e:
            logger.error(f"Failed to insert chunks: {e}")
            return False

    async def find_one(self, query: dict) -> Optional[Chunk]:
        """Retrieves a single chunk matching the query and converts it to a Model."""
        try:
            async with self.db_client() as session:
                stmt = select(PGChunk)
                if "chunk_uuid" in query:
                    stmt = stmt.where(PGChunk.chunk_uuid == query["chunk_uuid"])
                elif "chunk_project_id" in query:
                    try:
                        project_id_int = int(query["chunk_project_id"])
                        stmt = stmt.where(PGChunk.chunk_project_id == project_id_int)
                    except (ValueError, TypeError):
                        project_id_val = query["chunk_project_id"]
                        if _is_valid_uuid(project_id_val):
                            cond = (PGProject.project_id == project_id_val) | (PGProject.project_uuid == project_id_val)
                        else:
                            cond = (PGProject.project_id == project_id_val)
                        stmt = stmt.join(PGProject).where(cond)
                elif "id" in query:
                    stmt = stmt.where(PGChunk.id == int(query["id"]))
                elif "_id" in query:
                    stmt = stmt.where(PGChunk.id == int(query["_id"]))

                result = await session.execute(stmt)
                db_chunk = result.scalars().first()
                if db_chunk:
                    return Chunk(
                        id=db_chunk.id,
                        chunk_uuid=str(db_chunk.chunk_uuid),
                        chunk_project_id=db_chunk.chunk_project_id,
                        chunk_asset_id=db_chunk.chunk_asset_id,
                        file_id=db_chunk.file_id,
                        chunk_order=db_chunk.chunk_order,
                        chunk_text=db_chunk.chunk_text,
                        chunk_metadata=db_chunk.chunk_metadata,
                        chunk_created_at=db_chunk.chunk_created_at,
                        chunk_updated_at=db_chunk.chunk_updated_at,
                        vector_id=db_chunk.vector_id
                    )
                return None
        except Exception as e:
            logger.error(f"Error in find_one for query {query}: {e}")
            return None

    async def find_all(self, query: Optional[dict] = None) -> List[Chunk]:
        """Retrieves all chunks matching the query and converts them to Models."""
        try:
            query = query or {}
            async with self.db_client() as session:
                stmt = select(PGChunk)
                if "chunk_uuid" in query:
                    stmt = stmt.where(PGChunk.chunk_uuid == query["chunk_uuid"])
                elif "chunk_project_id" in query:
                    try:
                        project_id_int = int(query["chunk_project_id"])
                        stmt = stmt.where(PGChunk.chunk_project_id == project_id_int)
                    except (ValueError, TypeError):
                        project_id_val = query["chunk_project_id"]
                        if _is_valid_uuid(project_id_val):
                            cond = (PGProject.project_id == project_id_val) | (PGProject.project_uuid == project_id_val)
                        else:
                            cond = (PGProject.project_id == project_id_val)
                        stmt = stmt.join(PGProject).where(cond)
                elif "id" in query:
                    stmt = stmt.where(PGChunk.id == int(query["id"]))
                elif "_id" in query:
                    stmt = stmt.where(PGChunk.id == int(query["_id"]))

                result = await session.execute(stmt)
                db_chunks = result.scalars().all()
                return [
                    Chunk(
                        id=db_chunk.id,
                        chunk_uuid=str(db_chunk.chunk_uuid),
                        chunk_project_id=db_chunk.chunk_project_id,
                        chunk_asset_id=db_chunk.chunk_asset_id,
                        file_id=db_chunk.file_id,
                        chunk_order=db_chunk.chunk_order,
                        chunk_text=db_chunk.chunk_text,
                        chunk_metadata=db_chunk.chunk_metadata,
                        chunk_created_at=db_chunk.chunk_created_at,
                        chunk_updated_at=db_chunk.chunk_updated_at,
                        vector_id=db_chunk.vector_id
                    )
                    for db_chunk in db_chunks
                ]
        except Exception as e:
            logger.error(f"Error in find_all for query {query}: {e}")
            return []

    async def find_paginated(self, query: Optional[dict] = None, page: int = 1, page_size: int = 10) -> List[Chunk]:
        """Retrieves chunks matching the query with pagination support."""
        try:
            query = query or {}
            skip = (page - 1) * page_size
            async with self.db_client() as session:
                stmt = select(PGChunk)
                if "chunk_uuid" in query:
                    stmt = stmt.where(PGChunk.chunk_uuid == query["chunk_uuid"])
                elif "chunk_project_id" in query:
                    try:
                        project_id_int = int(query["chunk_project_id"])
                        stmt = stmt.where(PGChunk.chunk_project_id == project_id_int)
                    except (ValueError, TypeError):
                        project_id_val = query["chunk_project_id"]
                        if _is_valid_uuid(project_id_val):
                            cond = (PGProject.project_id == project_id_val) | (PGProject.project_uuid == project_id_val)
                        else:
                            cond = (PGProject.project_id == project_id_val)
                        stmt = stmt.join(PGProject).where(cond)
                elif "id" in query:
                    stmt = stmt.where(PGChunk.id == int(query["id"]))
                elif "_id" in query:
                    stmt = stmt.where(PGChunk.id == int(query["_id"]))

                stmt = stmt.offset(skip).limit(page_size)
                result = await session.execute(stmt)
                db_chunks = result.scalars().all()
                return [
                    Chunk(
                        id=db_chunk.id,
                        chunk_uuid=str(db_chunk.chunk_uuid),
                        chunk_project_id=db_chunk.chunk_project_id,
                        chunk_asset_id=db_chunk.chunk_asset_id,
                        file_id=db_chunk.file_id,
                        chunk_order=db_chunk.chunk_order,
                        chunk_text=db_chunk.chunk_text,
                        chunk_metadata=db_chunk.chunk_metadata,
                        chunk_created_at=db_chunk.chunk_created_at,
                        chunk_updated_at=db_chunk.chunk_updated_at,
                        vector_id=db_chunk.vector_id
                    )
                    for db_chunk in db_chunks
                ]
        except Exception as e:
            logger.error(f"Error in find_paginated for query {query}: {e}")
            return []

    async def get_project_chunks(self, project_id: Any) -> List[Chunk]:
        """Retrieves all chunks for a specific project."""
        return await self.find_all({"chunk_project_id": project_id})

    async def delete_project_chunks(self, project_id: Any) -> int:
        """Deletes all chunks associated with a project. Returns the count."""
        try:
            async with self.db_client() as session:
                async with session.begin():
                    try:
                        project_id_int = int(project_id)
                        stmt = select(PGChunk).where(PGChunk.chunk_project_id == project_id_int)
                    except (ValueError, TypeError):
                        if _is_valid_uuid(project_id):
                            cond = (PGProject.project_id == project_id) | (PGProject.project_uuid == project_id)
                        else:
                            cond = (PGProject.project_id == project_id)
                        stmt = select(PGChunk).join(PGProject).where(cond)
                    result = await session.execute(stmt)
                    db_chunks = result.scalars().all()
                    count = len(db_chunks)
                    for c in db_chunks:
                        await session.delete(c)
                    return count
        except Exception as e:
            logger.error(f"Failed to delete chunks for project {project_id}: {e}")
            return 0

    async def get_project_chunks_count(self, project_id: Any) -> int:
        """Returns the total count of chunks for a specific project."""
        try:
            async with self.db_client() as session:
                try:
                    project_id_int = int(project_id)
                    stmt = select(func.count(PGChunk.id)).where(PGChunk.chunk_project_id == project_id_int)
                except (ValueError, TypeError):
                    if _is_valid_uuid(project_id):
                        cond = (PGProject.project_id == project_id) | (PGProject.project_uuid == project_id)
                    else:
                        cond = (PGProject.project_id == project_id)
                    stmt = select(func.count(PGChunk.id)).join(PGProject).where(cond)
                result = await session.execute(stmt)
                return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error getting total chunks count for project {project_id}: {e}")
            return 0

