from typing import Optional
from .LLM_Interface import BaseLLM, LLMResponse



class OllamaProvider(BaseLLM):
    """
    This is the specific class for local models running on Ollama.
    It inherits the rules from BaseLLM.
    """
    def __init__(self, api_url: str, 
                 default_input_max_characters: int = 1000, 
                 default_generation_max_output_tokens: int = 1000, 
                 default_generation_temperature: float = 0.1):
        
        # Ollama usually needs a base_url (like http://localhost:11434), not an API key
        super().__init__(api_url=api_url, 
                         default_input_max_characters=default_input_max_characters, 
                         default_generation_max_output_tokens=default_generation_max_output_tokens, 
                         default_generation_temperature=default_generation_temperature)
        
        if not self.api_url:
            raise ValueError("OllamaProvider requires an api_url (base_url)")

        self.generation_model_id = "llama3"
        self.embedding_model_id = "nomic-embed-text"

    def generate_text(self, prompt: str, chat_history: list=None, max_output_tokens: Optional[int]=None, temperature: Optional[float] = None) -> LLMResponse:
        """Generate text using a local Ollama model."""
        temp = temperature if temperature is not None else self.default_generation_temperature
        tokens = max_output_tokens if max_output_tokens is not None else self.default_generation_max_output_tokens
        
        # TODO: Add real Ollama connection code here later
        return LLMResponse(
            text=f"Simulated Ollama ({self.generation_model_id}) generation for: {prompt[:20]}...",
            tokens=tokens,
            metadata={"provider": "ollama", "model": self.generation_model_id, "temperature": temp}
        )

    def embed_text(self, text: str, document_type: Optional[str] = None) -> list[float]:
        """Convert text into a vector using Ollama embeddings."""
        # TODO: Add real Ollama embedding code here later
        return [0.4, 0.5, 0.6]

    def construct_prompt(self, prompt: str, role: str) -> dict:
        """Format the message for Ollama format."""
        return {"role": role, "content": prompt}

class GeminiProvider(BaseLLM):
    """
    This is the specific class for Google's Gemini models.
    Excellent for RAG due to its massive context window (up to 2M tokens).
    """
    def __init__(self, api_key: str, api_url: Optional[str] = None, 
                 default_input_max_characters: int = 1000, 
                 default_generation_max_output_tokens: int = 1000, 
                 default_generation_temperature: float = 0.1):
        
        super().__init__(api_key=api_key, api_url=api_url, 
                         default_input_max_characters=default_input_max_characters, 
                         default_generation_max_output_tokens=default_generation_max_output_tokens, 
                         default_generation_temperature=default_generation_temperature)
        
        # Gemini requires an API key
        if not self.api_key:
            raise ValueError("GeminiProvider requires an api_key")

        self.generation_model_id = "gemini-1.5-flash"
        self.embedding_model_id = "text-embedding-004"

    def generate_text(self, prompt: str, chat_history: list=None, max_output_tokens: Optional[int]=None, temperature: Optional[float] = None) -> LLMResponse:
        """Generate text using Google Gemini API."""
        temp = temperature if temperature is not None else self.default_generation_temperature
        tokens = max_output_tokens if max_output_tokens is not None else self.default_generation_max_output_tokens
        
        # TODO: Add real Gemini connection code here later (e.g. using google-generativeai package)
        return LLMResponse(
            text=f"Simulated Gemini ({self.generation_model_id}) generation for: {prompt[:20]}...",
            tokens=tokens,
            metadata={"provider": "gemini", "model": self.generation_model_id, "temperature": temp}
        )

    def embed_text(self, text: str, document_type: Optional[str] = None) -> list[float]:
        """Convert text into a vector using Gemini embeddings (like text-embedding-004)."""
        # TODO: Add real Gemini embedding code here later
        return [0.7, 0.8, 0.9]

    def construct_prompt(self, prompt: str, role: str) -> dict:
        """
        Format the message for Gemini format. 
        Note: Gemini usually uses 'model' instead of 'assistant'.
        """
        return {"role": role, "content": prompt}
