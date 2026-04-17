from .base_controller import BaseController
from .project_controller import project_controller
import os
import logging
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from models import ProcessingEnum
from typing import List, Optional
from dataclasses import dataclass

# Production-grade logging setup
logger = logging.getLogger(__name__)

@dataclass
class Document:
    """
    Standard Data Class for document objects within the processing pipeline.
    Ensures compatibility with downstream RAG and Vector DB interfaces.
    """
    page_content: str
    metadata: dict

class ProcessController(BaseController):
    """
    ProcessController handles the ingestion, loading, and chunking of 
    diverse file formats (PDF, TXT) into manageable pieces for AI processing.
    """

    def __init__(self, project_id: str):
        super().__init__()
        self.project_id = project_id
        # Ensure project path is retrieved via the dedicated project_controller instance
        self.project_path = project_controller.get_project_path(project_id=project_id)

    def get_file_extension(self, file_id: str) -> str:
        """Extracts and returns the file extension from the provided file_id (filename)."""
        return os.path.splitext(file_id)[-1]

    def get_file_loader(self, file_id: str):
        """
        Factory method to determine and initialize the appropriate LangChain document loader.
        Currently supports structured TXT and PDF formats.
        """
        file_ext = self.get_file_extension(file_id=file_id)
        file_path = os.path.join(self.project_path, file_id)

        # Critical: Verify file existence before attempting to initialize loaders
        if not os.path.exists(file_path):
            logger.error(f"Processing failed: File '{file_path}' does not exist.")
            return None

        if file_ext == ProcessingEnum.TXT.value:
            return TextLoader(file_path, encoding="utf-8")

        if file_ext == ProcessingEnum.PDF.value:
            return PyMuPDFLoader(file_path)
        
        logger.warning(f"Processing aborted: Extension '{file_ext}' is not supported yet.")
        return None

    def get_file_content(self, file_id: str) -> Optional[List]:
        """
        Utilizes the resolved loader to read the file content into memory.
        Returns a list of LangChain Document objects.
        """
        loader = self.get_file_loader(file_id=file_id)
        if loader:
            try:
                return loader.load()
            except Exception as e:
                logger.error(f"Error while loading content for file '{file_id}': {str(e)}")
        return None

    def process_file_content(self, file_content: list, file_id: str,
                            chunk_size: int = 800, overlap_size: int = 150) -> List[Document]:
        """
        Main orchestration logic for splitting raw file content into text chunks.
        Uses RecursiveCharacterTextSplitter for optimal RAG performance.
        """

        # Initialize RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap_size,
            length_function=len,
            is_separator_regex=False,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Split the content
        return splitter.split_documents(file_content)


    def process_file(self, file_id: str, chunk_size: int = 800, overlap_size: int = 150, do_reset: int = 0):
        """
        Production Entry Point: Coordinates the full ingestion and transformation workflow.
        Returns a status tuple (success_flag, result_message, optional_chunks).
        """
        logger.info(f"Initiating processing sequence for Project: {self.project_id} | File: {file_id}")
        
        # Load raw content
        file_content = self.get_file_content(file_id=file_id)
        if file_content is None:
            return False, "File load failed: Resource not found or format unsupported.", None
            
        # Execute chunking transformation
        chunks = self.process_file_content(
            file_content=file_content,
            file_id=file_id,
            chunk_size=chunk_size,
            overlap_size=overlap_size
        )
        
        logger.info(f"Processing Complete: {file_id} decomposed into {len(chunks)} chunks.")
        return True, f"File successfully processed into {len(chunks)} chunks.", chunks

    