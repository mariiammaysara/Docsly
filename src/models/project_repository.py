from .base_data_model import BaseDataModel
from .db_schemas import Project
from .db_schemas.docsly import PGProject
from .enums import ProcessingStatusEnum
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

class ProjectRepository(BaseDataModel):
    """
    Repository class for the 'projects' table in PostgreSQL.
    Handles data access logic for Project entities.
    """
    def __init__(self, db_client):
        super().__init__(db_client=db_client)
        
    @classmethod
    async def create(cls, db_client):
        """Async factory method to create and initialize the repository."""
        instance = cls(db_client)
        return instance

    async def create_project(self, project: Project) -> Project:
        """Creates a new project record and returns the instance."""
        try:
            async with self.db_client() as session:
                async with session.begin():
                    db_project = PGProject(
                        project_id=project.project_id,
                        project_uuid=project.project_uuid,
                        project_pushed_at=project.project_pushed_at,
                        project_updated_at=project.project_updated_at,
                        processing_status=project.processing_status.value
                    )
                    session.add(db_project)
                    await session.flush()
                    project.id = db_project.id
                    return project
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            raise e

    async def get_project_or_create_one(self, project_id: str) -> Project:
        """
        Retrieves a project by its human-readable ID, 
        or creates a new one atomically using get-or-create logic.
        """
        try:
            async with self.db_client() as session:
                async with session.begin():
                    stmt = select(PGProject).where(PGProject.project_id == project_id)
                    result = await session.execute(stmt)
                    db_project = result.scalars().first()
                    if not db_project:
                        db_project = PGProject(
                            project_id=project_id,
                            processing_status=ProcessingStatusEnum.PENDING.value
                        )
                        session.add(db_project)
                        try:
                            await session.flush()
                        except IntegrityError:
                            await session.rollback()
                            stmt = select(PGProject).where(PGProject.project_id == project_id)
                            result = await session.execute(stmt)
                            db_project = result.scalars().first()
                    
                    return Project(
                        id=db_project.id,
                        project_id=db_project.project_id,
                        project_uuid=str(db_project.project_uuid),
                        project_pushed_at=db_project.project_pushed_at,
                        project_updated_at=db_project.project_updated_at,
                        processing_status=ProcessingStatusEnum(db_project.processing_status)
                    )
        except Exception as e:
            logger.error(f"Error in get_project_or_create_one for {project_id}: {e}")
            raise e

    async def find_one(self, query: dict) -> Optional[Project]:
        """Retrieves a single project matching the query."""
        try:
            async with self.db_client() as session:
                stmt = select(PGProject)
                if "project_id" in query:
                    stmt = stmt.where(PGProject.project_id == query["project_id"])
                elif "project_uuid" in query:
                    stmt = stmt.where(PGProject.project_uuid == query["project_uuid"])
                elif "_id" in query:
                    stmt = stmt.where(PGProject.id == int(query["_id"]))
                elif "id" in query:
                    stmt = stmt.where(PGProject.id == int(query["id"]))
                    
                result = await session.execute(stmt)
                db_project = result.scalars().first()
                if db_project:
                    return Project(
                        id=db_project.id,
                        project_id=db_project.project_id,
                        project_uuid=str(db_project.project_uuid),
                        project_pushed_at=db_project.project_pushed_at,
                        project_updated_at=db_project.project_updated_at,
                        processing_status=ProcessingStatusEnum(db_project.processing_status)
                    )
                return None
        except Exception as e:
            logger.error(f"Error in find_one for query {query}: {e}")
            return None

    async def find_all(self, query: Optional[dict] = None) -> List[Project]:
        """Retrieves all projects matching the query and converts them to Models."""
        try:
            query = query or {}
            async with self.db_client() as session:
                stmt = select(PGProject)
                if "project_id" in query:
                    stmt = stmt.where(PGProject.project_id == query["project_id"])
                elif "project_uuid" in query:
                    stmt = stmt.where(PGProject.project_uuid == query["project_uuid"])
                elif "_id" in query:
                    stmt = stmt.where(PGProject.id == int(query["_id"]))
                elif "id" in query:
                    stmt = stmt.where(PGProject.id == int(query["id"]))
                    
                result = await session.execute(stmt)
                db_projects = result.scalars().all()
                return [
                    Project(
                        id=p.id,
                        project_id=p.project_id,
                        project_uuid=str(p.project_uuid),
                        project_pushed_at=p.project_pushed_at,
                        project_updated_at=p.project_updated_at,
                        processing_status=ProcessingStatusEnum(p.processing_status)
                    )
                    for p in db_projects
                ]
        except Exception as e:
            logger.error(f"Error in find_all for query {query}: {e}")
            return []

    async def find_paginated(self, query: Optional[dict] = None, page: int = 1, page_size: int = 10) -> List[Project]:
        """Retrieves projects matching the query with pagination support."""
        try:
            query = query or {}
            skip = (page - 1) * page_size
            async with self.db_client() as session:
                stmt = select(PGProject)
                if "project_id" in query:
                    stmt = stmt.where(PGProject.project_id == query["project_id"])
                elif "project_uuid" in query:
                    stmt = stmt.where(PGProject.project_uuid == query["project_uuid"])
                elif "_id" in query:
                    stmt = stmt.where(PGProject.id == int(query["_id"]))
                elif "id" in query:
                    stmt = stmt.where(PGProject.id == int(query["id"]))
                
                stmt = stmt.offset(skip).limit(page_size)
                result = await session.execute(stmt)
                db_projects = result.scalars().all()
                return [
                    Project(
                        id=p.id,
                        project_id=p.project_id,
                        project_uuid=str(p.project_uuid),
                        project_pushed_at=p.project_pushed_at,
                        project_updated_at=p.project_updated_at,
                        processing_status=ProcessingStatusEnum(p.processing_status)
                    )
                    for p in db_projects
                ]
        except Exception as e:
            logger.error(f"Error in find_paginated for query {query}: {e}")
            return []
