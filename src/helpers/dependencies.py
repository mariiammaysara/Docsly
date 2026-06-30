from fastapi import Request
from src.stores.vectordb.VectorDB_Interface import BaseVectorDB

async def get_vector_db(request: Request) -> BaseVectorDB:
    """Dependency to retrieve the configured Vector Database client."""
    return request.app.vectordb_client

async def get_generation_client(request: Request):
    """Dependency to retrieve the configured LLM generation client."""
    return request.app.generation_client

async def get_embedding_client(request: Request):
    """Dependency to retrieve the configured LLM embedding client."""
    return request.app.embedding_client

async def get_template_parser(request: Request):
    """Dependency to retrieve the configured template parser."""
    return request.app.template_parser
