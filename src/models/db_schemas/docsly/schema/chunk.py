from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from .docsly_base import SQLAlchemyBase

class PGChunk(SQLAlchemyBase):
    __tablename__ = 'chunks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    chunk_project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    chunk_asset_id = Column(Integer, ForeignKey('assets.id', ondelete='SET NULL'), nullable=True)
    file_id = Column(String, nullable=False)
    chunk_order = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_metadata = Column(JSONB, default=dict, nullable=False)
    chunk_created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    chunk_updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    vector_id = Column(String, nullable=True)

    project = relationship("PGProject", back_populates="chunks")
    asset = relationship("PGAsset", back_populates="chunks")

    __table_args__ = (
        Index('ix_chunk_project_id', chunk_project_id),
        Index('ix_chunk_asset_id', chunk_asset_id),
    )


