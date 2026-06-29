from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .docsly_base import SQLAlchemyBase

class PGProject(SQLAlchemyBase):
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, unique=True, nullable=False, index=True)
    project_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    project_pushed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    project_updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    processing_status = Column(String, default="PENDING", nullable=False)

    assets = relationship("PGAsset", back_populates="project", cascade="all, delete-orphan")
    chunks = relationship("PGChunk", back_populates="project", cascade="all, delete-orphan")

