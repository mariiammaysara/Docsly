from .base_controller import BaseController
from src.models.db_schemas.retrieval import RetrievedDocument
from typing import List

class RetrievalController(BaseController):
    """
    Controller responsible for retrieving relevant documents 
    using semantic search.
    """
    def __init__(self, embedding_client, vectordb_client):
        super().__init__()
        self.embedding_client = embedding_client
        self.vectordb_client = vectordb_client

    async def search(self, query: str, project_id: str, limit: int = 5) -> List[RetrievedDocument]:
        """
        Perform semantic search for a given query within a project.
        
        Steps:
        1. Convert the search query into a vector (Embedding).
        2. Use the vector to find similar chunks in the Vector DB.
        """
        # Generate embedding for the query string
        query_vector = self.embedding_client.embed_text(query)
        
        # Search the vector database (using project_id as the collection name)
        results = await self.vectordb_client.search_by_vector(
            collection_name=project_id,
            vector=query_vector,
            limit=limit
        )
        
        return results
