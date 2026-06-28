from .base_controller import BaseController
from .project_controller import project_controller
import os
import logging
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.models import ProcessingEnum
from typing import List, Optional
from dataclasses import dataclass

# Setup logging to print messages in the console
logger = logging.getLogger(__name__)

@dataclass
class Document:
    """
    A simple class to hold the text of a document and its details.
    This helps us send data to the AI and database easily.
    """
    page_content: str
    metadata: dict

class ProcessController(BaseController):
    """
    This Controller manages reading files (like PDF or TXT) 
    and breaking them into smaller parts (chunks) so the AI can read them.
    """

    def __init__(self, project_id: str, embedding_client = None, vectordb_client = None):
        super().__init__()
        self.project_id = project_id
        self.embedding_client = embedding_client
        self.vectordb_client = vectordb_client
        # Get the folder where this project's files are stored
        self.project_path = project_controller.get_project_path(project_id=project_id)

    def get_file_extension(self, file_id: str) -> str:
        """Find out the file type (e.g., '.pdf' or '.txt') from its name."""
        return os.path.splitext(file_id)[-1]

    def get_file_loader(self, file_id: str):
        """
        Choose the right tool (loader) to read the file.
        It uses TextLoader for text files and PyMuPDFLoader for PDFs.
        """
        file_ext = self.get_file_extension(file_id=file_id)
        file_path = os.path.join(self.project_path, file_id)

        # Check if the file actually exists before trying to open it
        if not os.path.exists(file_path):
            logger.error(f"Error: The file '{file_path}' does not exist.")
            return None

        # Return the correct loader based on the file type
        if file_ext == ProcessingEnum.TXT.value:
            logger.info(f"Using TextLoader to read: {file_path}")
            return TextLoader(file_path, encoding="utf-8")

        if file_ext == ProcessingEnum.PDF.value:
            logger.info(f"Using PyMuPDFLoader to read: {file_path}")
            return PyMuPDFLoader(file_path)
        
        # If the file type is not supported
        logger.warning(f"Stop: The file type '{file_ext}' is not supported.")
        return None

    def get_file_content(self, file_id: str) -> Optional[List]:
        """
        Read the file and load its text into memory.
        Returns a list of Documents or None if it fails.
        """
        loader = self.get_file_loader(file_id=file_id)
        if loader:
            try:
                return loader.load()
            except Exception as e:
                logger.error(f"Failed to read file '{file_id}'. Error: {str(e)}")
        return None

    def process_file_content(self, file_content: list, file_id: str,
                            chunk_size: int = 800, overlap_size: int = 150) -> List[Document]:
        """
        Break the long text into smaller pieces (chunks).
        This is important because AI cannot read a huge book all at once.
        """

        # Setup the tool that cuts the text
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap_size, # Keep some shared text between chunks so we don't lose context
            length_function=len,
            is_separator_regex=False,
            separators=["\n\n", "\n", " ", ""] # Try splitting by paragraphs first, then sentences, then words
        )
        
        # Cut the text and return the chunks
        return splitter.split_documents(file_content)

    async def process_file(self, file_id: str, chunk_size: int = 800, overlap_size: int = 150, do_reset: int = 0):
        """
        The main function that does everything:
        1. Reads the file.
        2. Breaks it into chunks.
        3. Generates embeddings and stores them in VectorDB.
        4. Returns the result.
        """
        logger.info(f"Starting to process file: {file_id} in project: {self.project_id}")
        
        # Step 1: Read the text
        file_content = self.get_file_content(file_id=file_id)
        if file_content is None:
            return False, "Failed to load the file.", None
            
        # Step 2: Cut the text into chunks
        chunks = self.process_file_content(
            file_content=file_content,
            file_id=file_id,
            chunk_size=chunk_size,
            overlap_size=overlap_size
        )
        
        # Step 3: Vectorization (If clients are provided)
        if self.embedding_client and self.vectordb_client:
            logger.info(f"Vectorizing {len(chunks)} chunks for project: {self.project_id}...")
            
            # Prepare data for VectorDB
            texts = [c.page_content for c in chunks]
            
            # Generate embeddings for all chunks at once (More efficient)
            vectors = self.embedding_client.embed_text(texts)
            
            # Ensure collection exists in VectorDB
            if vectors and len(vectors) > 0:
                embedding_size = len(vectors[0]) 
                
                # Standardized collection name (consistent with NLPController)
                collection_name = f"collection_{embedding_size}_{self.project_id}".strip()
                
                await self.vectordb_client.create_collection(
                    collection_name=collection_name,
                    embedding_size=embedding_size,
                    do_reset=bool(do_reset)
                )
                
                # Insert many
                await self.vectordb_client.insert_many(
                    collection_name=collection_name,
                    texts=texts,
                    vectors=vectors,
                    metadata=[c.metadata for c in chunks]
                )
                logger.info(f"Successfully stored {len(chunks)} vectors in VectorDB collection: {collection_name}")

        # Step 4: Finish and return the chunks
        logger.info(f"Success: File '{file_id}' was cut into {len(chunks)} chunks.")
        return True, f"File successfully processed and vectorized into {len(chunks)} chunks.", chunks
