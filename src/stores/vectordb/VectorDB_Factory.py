from .VectorDB_Enums import VectorDBEnums
from .VectorDB_Interface import BaseVectorDB
from ..providers.QdrantProvider import QdrantProvider 
from typing import Any, Optional

class VectorDBProviderFactory:
    """
    Factory to manage and create Vector Database providers.
    """
    def __init__(self, config, db_client: Optional[Any] = None):
        """
        Initialize the factory with global config and an optional database client 
        (like a SQLAlchemy session for PGVector).
        """
        self.config = config
        self.db_client = db_client

    def create(self, provider: str) -> BaseVectorDB:
        """
        Create the requested Vector DB provider based on the configuration.
        """
        if provider == VectorDBEnums.QDRANT.value:
            # Qdrant doesn't need db_client, but we pass config
            return QdrantProvider(config=self.config)
            
        elif provider == VectorDBEnums.PGVECTOR.value:
            # PGVector will need the db_client (Postgres connection)
            # from ..providers.PgVectorProvider import PgVectorProvider
            # return PgVectorProvider(config=self.config, db_client=self.db_client)
            pass
            
        return None
