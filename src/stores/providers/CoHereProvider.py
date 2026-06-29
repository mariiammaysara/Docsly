from typing import Optional, List, Union
import logging
import cohere
from src.stores.llm.LLM_Interface import BaseLLM, LLMResponse
from src.stores.llm.LLM_Enums import CoHereEnums, DocumentTypeEnum

class CoHereProvider(BaseLLM):
    """
    Real implementation for Cohere using their official SDK.
    This class handles connecting to Cohere to generate text and embeddings.
    """
    def __init__(self, api_key: str, api_url: Optional[str] = None, 
                 default_input_max_characters: int = 1000, 
                 default_generation_max_output_tokens: int = 1000, 
                 default_generation_temperature: float = 0.1):
        
        super().__init__(api_key=api_key, api_url=api_url, 
                         default_input_max_characters=default_input_max_characters, 
                         default_generation_max_output_tokens=default_generation_max_output_tokens, 
                         default_generation_temperature=default_generation_temperature)
        
        # Stop the program if the user forgot to add the API key
        if not self.api_key:
            raise ValueError("CoHereProvider requires an api_key")

        # Create the Cohere client to talk to the API
        self.client = cohere.Client(api_key=self.api_key)
        # Setup logging to print messages in the console
        self.logger = logging.getLogger(__name__)

        # Set default models
        self.generation_model_id = "command-r-08-2024" 
        self.embedding_model_id = "embed-english-v3.0" 

    def set_generation_model(self, model_id: str):
        """Change the model used for generating text."""
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int = None):
        """Change the model used for converting text into vectors."""
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

    def process_text(self, text: str):
        """
        Cut the text if it is too long. 
        This protects us from Cohere token limit errors and saves money.
        """
        return text[:self.default_input_max_characters].strip()

    def generate_text(self, prompt: str, chat_history: list=None, max_output_tokens: Optional[int]=None, temperature: Optional[float] = None) -> LLMResponse:
        """
        Send a message to Cohere and get a text response.
        """
        # Safety check: ensure the client is ready
        if not self.client:
            self.logger.error("CoHere client was not set")
            return LLMResponse(text="")

        # Use provided settings, or fallback to defaults
        temp = temperature if temperature is not None else self.default_generation_temperature
        tokens = max_output_tokens if max_output_tokens is not None else self.default_generation_max_output_tokens
        
        self.logger.info(f"Initiating CoHere generation using model: {self.generation_model_id}")

        try:
            # We use process_text to ensure we don't send too much text at once
            response = self.client.chat(
                model=self.generation_model_id,
                chat_history=chat_history if chat_history else [],
                message=self.process_text(prompt),
                temperature=temp,
                max_tokens=tokens
            )

            # Safety check: ensure we received a valid response
            if not response or not response.text:
                self.logger.error("Error while generating text with CoHere")
                return LLMResponse(text="")
            
            self.logger.info(f"Successfully generated text with CoHere")

            # Return our standardized object
            return LLMResponse(
                text=response.text,
                metadata={"provider": "cohere", "model": self.generation_model_id}
            )
        except Exception as e:
            self.logger.error(f"CoHere API Error: {str(e)}")
            return LLMResponse(text="")

    def embed_text(self, text: Union[str, List[str]], document_type: str = None) -> list[float]:
        """
        Convert text (or a list of texts) into numbers (vectors) using Cohere.
        """
        # Safety check: ensure the client is ready
        if not self.client:
            self.logger.error("CoHere client was not set")
            return []
        
        # Ensure we always process a list, even if the user sends a single string
        if isinstance(text, str):
            text = [text]
            
        # Determine the input type (Cohere requires this to be specified for embeddings)
        input_type = CoHereEnums.DOCUMENT.value
        if document_type == DocumentTypeEnum.QUERY.value:
            input_type = CoHereEnums.QUERY.value

        self.logger.info(f"Initiating CoHere embedding for {len(text)} document(s) using model: {self.embedding_model_id}")

        try:
            # Call the Cohere API to get embeddings
            response = self.client.embed(
                model=self.embedding_model_id,
                texts=[self.process_text(t) for t in text],
                input_type=input_type,
                embedding_types=['float'],
            )

            # Safety check: ensure we received valid data
            if not response or not response.embeddings or not response.embeddings.float:
                self.logger.error("Error while embedding text with CoHere")
                return []
            
            self.logger.info("Successfully generated embeddings with CoHere")

            # Return a list of vectors (Batching support)
            return [f for f in response.embeddings.float]
        except Exception as e:
            self.logger.error(f"CoHere Embedding Error: {str(e)}")
            return []

    def construct_prompt(self, prompt: str, role: str):
        """
        Format the message dictionary exactly how Cohere expects it.
        """
        return {
            "role": role,
            "text": prompt,
        }
