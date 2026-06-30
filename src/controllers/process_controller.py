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

    def __init__(self, project_id: str):
        super().__init__()
        self.project_id = project_id
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
        from src.helpers.config import get_settings
        settings = get_settings()

        # Choose splitting tool based on config
        if getattr(settings, 'TEXT_SPLITTER_BACKEND', 'RECURSIVE').upper() == 'NLTK':
            import nltk
            # Safely download required tokenizer packages if missing
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt', quiet=True)
            try:
                nltk.data.find('tokenizers/punkt_tab')
            except LookupError:
                nltk.download('punkt_tab', quiet=True)

            from langchain_text_splitters import NLTKTextSplitter
            splitter = NLTKTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=overlap_size
            )
        else:
            # Setup the tool that cuts the text recursively
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
        Reads a file and splits it into text chunks.
        Responsible ONLY for file I/O and text splitting.
        VectorDB embedding and indexing is handled separately by NLPController.
        """
        logger.info(f"Starting to process file: {file_id} in project: {self.project_id}")
        
        # Step 1: Read the text from disk
        file_content = self.get_file_content(file_id=file_id)
        if file_content is None:
            return False, "Failed to load the file.", None
            
        # Step 2: Split the text into chunks
        chunks = self.process_file_content(
            file_content=file_content,
            file_id=file_id,
            chunk_size=chunk_size,
            overlap_size=overlap_size
        )
        
        logger.info(f"Success: File '{file_id}' was split into {len(chunks)} chunks.")
        return True, f"File successfully processed into {len(chunks)} chunks.", chunks
