from enum import Enum

class LLMEnums(Enum):
    """Names of the AI companies/models we support."""
    OPENAI = "OPENAI"
    COHERE = "COHERE"
    OLLAMA = "OLLAMA" 
    GEMINI = "GEMINI" # Added Google Gemini

class OpenAIEnums(Enum):
    """Standard roles used by OpenAI."""
    SYSTEM = "system"       
    USER = "user"           
    ASSISTANT = "assistant" 

class GeminiEnums(Enum):
    """Standard roles used by Google Gemini."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "model" # Gemini uses 'model' instead of 'assistant'

class CoHereEnums(Enum):
    """Standard roles and types used by Cohere."""
    SYSTEM = "SYSTEM"
    USER = "USER"
    ASSISTANT = "CHATBOT"
    DOCUMENT = "search_document" 
    QUERY = "search_query"       

class DocumentTypeEnum(Enum):
    """Types of text we are processing."""
    DOCUMENT = "document" 
    QUERY = "query"       
