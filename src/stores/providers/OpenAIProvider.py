from typing import Optional, List, Union
import logging
from openai import OpenAI
from src.stores.llm.LLM_Interface import BaseLLM, LLMResponse
from src.stores.llm.LLM_Enums import OpenAIEnums

class OpenAIProvider(BaseLLM):
    """
    Real implementation for OpenAI using their official Python SDK.
    This class handles connecting to OpenAI to generate text and embeddings.
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
            raise ValueError("OpenAIProvider requires an api_key")

        # Create the OpenAI client to talk to the API
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_url if self.api_url and len(self.api_url) else None
        )
        # Setup logging to print messages in the console
        self.logger = logging.getLogger(__name__)

        # Set default models
        self.generation_model_id = "gpt-4-turbo" 
        self.embedding_model_id = "text-embedding-3-small" 

    def set_generation_model(self, model_id: str):
        """Change the model used for generating text."""
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str):
        """Change the model used for converting text into vectors."""
        self.embedding_model_id = model_id

    def process_text(self, text: str):
        """
        Cut the text if it is too long. 
        This protects us from OpenAI token limit errors and saves money.
        """
        return text[:self.default_input_max_characters].strip()

    def generate_text(self, prompt: str, chat_history: list=None, max_output_tokens: Optional[int]=None, temperature: Optional[float] = None) -> LLMResponse:
        """
        Send a message to OpenAI and get a text response.
        """
        # Safety check: ensure the client and model are ready
        if not self.client:
            self.logger.error("OpenAI client was not set")
            return LLMResponse(text="")

        if not self.generation_model_id:
            self.logger.error("Generation model for OpenAI was not set")
            return LLMResponse(text="")

        # Use provided settings, or fallback to defaults
        temp = temperature if temperature is not None else self.default_generation_temperature
        tokens = max_output_tokens if max_output_tokens is not None else self.default_generation_max_output_tokens
        
        # Prepare the list of messages for the chat
        messages = chat_history if chat_history else []
        messages.append(self.construct_prompt(prompt=prompt, role=OpenAIEnums.USER.value))

        self.logger.info(f"Initiating OpenAI generation using model: {self.generation_model_id}")

        try:
            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model=self.generation_model_id,
                messages=messages,
                temperature=temp,
                max_tokens=tokens
            )

            # Safety check: ensure we received a valid response
            if not response or not response.choices or len(response.choices) == 0 or not response.choices[0].message:
                self.logger.error("Error while generating text with OpenAI")
                return LLMResponse(text="")
            
            # Extract the text and the number of tokens used
            generated_text = response.choices[0].message.content
            usage_tokens = response.usage.total_tokens if response.usage else 0

            self.logger.info(f"Successfully generated text with OpenAI (Tokens used: {usage_tokens})")

            # Return our standardized object
            return LLMResponse(
                text=generated_text,
                tokens=usage_tokens,
                metadata={"provider": "openai", "model": self.generation_model_id}
            )
        except Exception as e:
            self.logger.error(f"OpenAI API Error: {str(e)}")
            return LLMResponse(text="")

    def embed_text(self, text: Union[str, List[str]], document_type: str = None) -> list[float]:
        """
        Convert text (or a list of texts) into numbers (vectors) using OpenAI.
        """
        # Safety check: ensure the client and model are ready
        if not self.client:
            self.logger.error("OpenAI client was not set")
            return []
        
        if not self.embedding_model_id:
            self.logger.error("Embedding model for OpenAI was not set")
            return []
        
        # Ensure we always process a list, even if the user sends a single string
        if isinstance(text, str):
            text = [text]

        self.logger.info(f"Initiating OpenAI embedding for {len(text)} document(s) using model: {self.embedding_model_id}")

        try:
            # Call the OpenAI API to get embeddings
            response = self.client.embeddings.create(
                model=self.embedding_model_id,
                input=[self.process_text(t) for t in text]
            )

            # Safety check: ensure we received valid data
            if not response or not response.data or len(response.data) == 0 or not response.data[0].embedding:
                self.logger.error("Error while embedding text with OpenAI")
                return []
            
            self.logger.info("Successfully generated embeddings with OpenAI")
            
            # Return a list of vectors (Batching support)
            return [rec.embedding for rec in response.data]
        except Exception as e:
            self.logger.error(f"OpenAI Embedding Error: {str(e)}")
            return []

    def construct_prompt(self, prompt: str, role: str):
        """
        Format the message dictionary exactly how OpenAI expects it.
        """
        return {
            "role": role,
            "content": prompt,
        }
