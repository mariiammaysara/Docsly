from typing import List, Optional, Dict, Any
from src.stores.vectordb.VectorDB_Interface import BaseVectorDB
from src.stores.vectordb.VectorDB_Enums import DistanceMethodEnums
from src.models.db_schemas.chunk import RetrievedChunk
from sqlalchemy import text
import uuid
import json
import logging

logger = logging.getLogger(__name__)

class PgVectorProvider(BaseVectorDB):
    """
    Implementation of VectorDBInterface for PostgreSQL with pgvector.
    Uses raw SQL execution over SQLAlchemy connection pool.
    """
    def __init__(self, config, db_client: Optional[Any] = None):
        super().__init__(config)
        self.db_client = db_client # This is the async_sessionmaker

    async def connect(self):
        """Verify extension vector exists."""
        if self.db_client:
            try:
                async with self.db_client() as session:
                    async with session.begin():
                        await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            except Exception as e:
                logger.error(f"Failed to connect / verify pgvector extension: {e}")

    async def disconnect(self):
        """No-op as engine is closed in main app lifespan."""
        pass

    async def is_collection_existed(self, collection_name: str) -> bool:
        """Check if a table exists for the collection."""
        safe_name = "".join([c for c in collection_name if c.isalnum() or c == "_"])
        async with self.db_client() as session:
            stmt = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = :table_name
                );
            """)
            result = await session.execute(stmt, {"table_name": safe_name})
            return bool(result.scalar())

    async def list_all_collections(self) -> List[str]:
        """List all collection tables."""
        async with self.db_client() as session:
            stmt = text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'collection_%';
            """)
            result = await session.execute(stmt)
            return [row[0] for row in result.all()]

    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get collection details."""
        safe_name = "".join([c for c in collection_name if c.isalnum() or c == "_"])
        async with self.db_client() as session:
            try:
                stmt = text(f"SELECT COUNT(*) FROM {safe_name};")
                result = await session.execute(stmt)
                count = result.scalar()
                return {"name": safe_name, "points_count": count}
            except Exception as e:
                logger.error(f"Failed to get collection info for {safe_name}: {e}")
                return {"name": safe_name, "points_count": 0}

    async def delete_collection(self, collection_name: str):
        """Drop collection table."""
        safe_name = "".join([c for c in collection_name if c.isalnum() or c == "_"])
        async with self.db_client() as session:
            async with session.begin():
                await session.execute(text(f"DROP TABLE IF EXISTS {safe_name};"))

    async def create_collection(self, collection_name: str, 
                                 embedding_size: int,
                                 do_reset: bool = False,
                                 distance_method: str = "cosine"):
        """Create a new collection table with vector dimensions."""
        safe_name = "".join([c for c in collection_name if c.isalnum() or c == "_"])
        if do_reset:
            await self.delete_collection(safe_name)

        async with self.db_client() as session:
            async with session.begin():
                await session.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {safe_name} (
                        id VARCHAR(36) PRIMARY KEY,
                        text TEXT NOT NULL,
                        embedding VECTOR({embedding_size}),
                        metadata JSONB
                    );
                """))
                
                # Check if distance method index should be created to optimize search
                index_name = f"idx_{safe_name}_embedding"
                op_class = "vector_cosine_ops"
                if distance_method == DistanceMethodEnums.EUCLIDEAN.value:
                    op_class = "vector_l2_ops"
                elif distance_method == DistanceMethodEnums.DOT.value:
                    op_class = "vector_ip_ops"

                await session.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS {index_name} 
                    ON {safe_name} USING hnsw (embedding {op_class});
                """))

    async def insert_one(self, collection_name: str, text: str, vector: list,
                         metadata: dict = None, 
                         record_id: str = None):
        """Insert a single record into the collection."""
        safe_name = "".join([c for c in collection_name if c.isalnum() or c == "_"])
        rec_id = record_id or str(uuid.uuid4())
        meta_json = json.dumps(metadata or {})
        vector_str = "[" + ",".join(map(str, vector)) + "]"

        async with self.db_client() as session:
            async with session.begin():
                stmt = text(f"""
                    INSERT INTO {safe_name} (id, text, embedding, metadata)
                    VALUES (:id, :text, CAST(:embedding AS vector), :metadata)
                    ON CONFLICT (id) DO UPDATE 
                    SET text = EXCLUDED.text, embedding = EXCLUDED.embedding, metadata = EXCLUDED.metadata;
                """)
                await session.execute(stmt, {
                    "id": rec_id,
                    "text": text,
                    "embedding": vector_str,
                    "metadata": meta_json
                })

    async def insert_many(self, collection_name: str, texts: list, 
                           vectors: list, metadata: list = None, 
                           record_ids: list = None, batch_size: int = 50):
        """Insert multiple records using batching."""
        safe_name = "".join([c for c in collection_name if c.isalnum() or c == "_"])
        async with self.db_client() as session:
            async with session.begin():
                for i in range(0, len(texts), batch_size):
                    batch_texts = texts[i:i+batch_size]
                    batch_vectors = vectors[i:i+batch_size]
                    batch_meta = metadata[i:i+batch_size] if metadata else [None]*len(batch_texts)
                    batch_ids = record_ids[i:i+batch_size] if record_ids else [None]*len(batch_texts)
                    
                    for txt, vec, meta, rec_id in zip(batch_texts, batch_vectors, batch_meta, batch_ids):
                        r_id = rec_id or str(uuid.uuid4())
                        meta_json = json.dumps(meta or {})
                        vector_str = "[" + ",".join(map(str, vec)) + "]"
                        
                        stmt = text(f"""
                            INSERT INTO {safe_name} (id, text, embedding, metadata)
                            VALUES (:id, :text, CAST(:embedding AS vector), :metadata)
                            ON CONFLICT (id) DO UPDATE 
                            SET text = EXCLUDED.text, embedding = EXCLUDED.embedding, metadata = EXCLUDED.metadata;
                        """)
                        await session.execute(stmt, {
                            "id": r_id,
                            "text": txt,
                            "embedding": vector_str,
                            "metadata": meta_json
                        })

    async def search_by_vector(self, collection_name: str, vector: list, limit: int) -> Optional[List[RetrievedChunk]]:
        """Search for the most similar vectors and return standardized results."""
        safe_name = "".join([c for c in collection_name if c.isalnum() or c == "_"])
        vector_str = "[" + ",".join(map(str, vector)) + "]"
        
        distance_method = getattr(self.config, 'VECTOR_DB_DISTANCE_METHOD', 'cosine').lower()
        if distance_method == "euclidean" or distance_method == "l2":
            op = "<->"  # L2 distance
            score_col = f"embedding {op} :query_vector"
        elif distance_method == "dot" or distance_method == "inner_product":
            op = "<#>"  # Negative inner product
            score_col = f"-(embedding {op} :query_vector)"
        else:
            op = "<=>"  # Cosine distance
            score_col = f"1 - (embedding {op} :query_vector)"

        async with self.db_client() as session:
            stmt = text(f"""
                SELECT id, text, metadata, {score_col} AS score
                FROM {safe_name}
                ORDER BY embedding {op} :query_vector
                LIMIT :limit;
            """)
            try:
                result = await session.execute(stmt, {
                    "query_vector": vector_str,
                    "limit": limit
                })
                rows = result.all()
            except Exception as e:
                logger.error(f"Search failed for collection {safe_name}: {e}")
                return None

        if not rows:
            return None

        return [
            RetrievedChunk(
                chunk_uuid=row[0],
                file_id=row[2].get("file_id", "") if row[2] else "",
                chunk_text=row[1],
                score=float(row[3]) if row[3] is not None else 0.0,
                chunk_metadata=row[2] or {}
            )
            for row in rows
        ]
