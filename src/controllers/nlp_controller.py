from .base_controller import BaseController
from src.models.db_schemas import Project, Chunk
from src.stores.llm.LLM_Enums import DocumentTypeEnum
from src.models.db_schemas.retrieval import RetrievedDocument
from typing import List, Tuple, Dict, Any
import json

class NLPController(BaseController):
    """
    Advanced NLP Controller based on the professor's version.
    Handles dynamic collection naming, robust search, and complex RAG prompts.
    """
    def __init__(self, vectordb_client, generation_client, embedding_client, template_parser):
        super().__init__()
        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser

    def create_collection_name(self, project_id: str):
        # Get vector size from embedding client or fallback to vector db default
        vector_size = getattr(self.embedding_client, 'embedding_model_size', 
                            getattr(self.vectordb_client, 'default_vector_size', 384))
        return f"collection_{vector_size}_{project_id}".strip()
    
    async def reset_vector_db_collection(self, project: Project):
        """Delete and recreate the project collection."""
        collection_name = self.create_collection_name(project_id=project.project_id)
        return await self.vectordb_client.delete_collection(collection_name=collection_name)
    
    async def get_vector_db_collection_info(self, project: Project):
        """Retrieve collection details and format them as a dictionary."""
        collection_name = self.create_collection_name(project_id=project.project_id)
        collection_info = await self.vectordb_client.get_collection_info(collection_name=collection_name)

        # Ensure JSON serializability
        return json.loads(
            json.dumps(collection_info, default=lambda x: x.__dict__ if hasattr(x, '__dict__') else str(x))
        )
    
    async def index_into_vector_db(self, project: Project, chunks: List[Chunk],
                                   chunks_ids: List[str], 
                                   do_reset: bool = False):
        """
        Embeds a list of chunks and inserts them into the vector database.
        """
        # step1: get collection name
        collection_name = self.create_collection_name(project_id=project.project_id)

        # step2: generate embeddings
        texts = [c.chunk_text for c in chunks]
        metadata = [c.chunk_metadata for c in chunks]
        vectors = self.embedding_client.embed_text(
            text=texts, 
            document_type=DocumentTypeEnum.DOCUMENT.value
        )

        # step3: create collection if not exists
        embedding_size = len(vectors[0]) if vectors else 0
        
        await self.vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=embedding_size,
            do_reset=do_reset,
        )

        # step4: insert into vector db
        await self.vectordb_client.insert_many(
            collection_name=collection_name,
            texts=texts,
            metadata=metadata,
            vectors=vectors,
            record_ids=chunks_ids,
        )

        return True

    async def search_vector_db_collection(self, project: Project, text: str, limit: int = 10):
        """
        Performs similarity search with robust vector handling.
        """
        # step1: get collection name
        collection_name = self.create_collection_name(project_id=project.project_id)

        # step2: get text embedding vector
        vectors = self.embedding_client.embed_text(
            text=text, 
            document_type=DocumentTypeEnum.QUERY.value
        )

        if not vectors or len(vectors) == 0:
            return False
        
        query_vector = vectors[0] if isinstance(vectors, list) else vectors

        if not query_vector:
            return False    

        # step3: do semantic search
        results = await self.vectordb_client.search_by_vector(
            collection_name=collection_name,
            vector=query_vector,
            limit=limit
        )

        return results if results else False
    
    async def answer_rag_question(self, project: Project, query: str, limit: int = 10):
        """
        Professional RAG answer generation with system prompt and chat history.
        """
        answer, full_prompt, chat_history = None, None, None

        # step1: retrieve related documents
        retrieved_documents = await self.search_vector_db_collection(
            project=project,
            text=query,
            limit=limit,
        )

        if not retrieved_documents or len(retrieved_documents) == 0:
            return answer, full_prompt, chat_history
        
        # step2: Construct LLM prompt parts
        system_prompt = self.template_parser.get("rag", "system_prompt")

        documents_prompts = "\n".join([
            self.template_parser.get("rag", "document_prompt", {
                    "doc_num": idx + 1,
                    "chunk_text": self.generation_client.process_text(doc.chunk_text),
            })
            for idx, doc in enumerate(retrieved_documents)
        ])

        footer_prompt = self.template_parser.get("rag", "footer_prompt", {
            "query": query
        })

        # step3: Construct Generation Client Prompts/History
        role = "system"
        if hasattr(self.generation_client, 'enums') and hasattr(self.generation_client.enums, 'SYSTEM'):
            role = self.generation_client.enums.SYSTEM.value

        chat_history = [
            self.generation_client.construct_prompt(
                prompt=system_prompt,
                role=role,
            )
        ]

        full_prompt = "\n\n".join([documents_prompts, footer_prompt])

        # step4: Retrieve the Answer
        answer_response = self.generation_client.generate_text(
            prompt=full_prompt,
            chat_history=chat_history
        )
        
        return answer_response.text, full_prompt, chat_history
