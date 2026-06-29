from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from .docsly_base import SQLAlchemyBase

class PGAsset(SQLAlchemyBase):
    __tablename__ = 'assets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    asset_project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    asset_name = Column(String, nullable=False)
    asset_type = Column(String, nullable=False)
    asset_size = Column(BigInteger, nullable=False)
    asset_path = Column(String, nullable=False)
    asset_config = Column(JSONB, default=dict, nullable=False)
    asset_pushed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("PGProject", back_populates="assets")
    chunks = relationship("PGChunk", back_populates="asset")

    __table_args__ = (
        Index('ix_asset_project_id', asset_project_id),
        Index('ix_asset_type', asset_type),
    )


