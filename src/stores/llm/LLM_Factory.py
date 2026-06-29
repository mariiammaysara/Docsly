from .LLM_Interface import BaseLLM
from .LLM_Enums import LLMEnums

class LLMProviderFactory:
    """
    This is the Factory (the manager).
    Instead of calling OpenAI or Ollama directly in our project, we tell this factory:
    "Give me an OpenAI model", and it builds it for us using the global settings.
    """
    def __init__(self, config):
        """
        Store the global project settings (like API keys from .env).
        We use 'getattr' later to safely get values without crashing if they are missing.
        """
        self.config = config

    def create(self, provider: str) -> BaseLLM:
        """
        Creates and returns the requested AI model (Provider).
        """
        instance = None

        if provider == LLMEnums.OPENAI.value:
            from ..providers.OpenAIProvider import OpenAIProvider
            instance = OpenAIProvider(
                api_key=self.config.OPENAI_API_KEY,
                api_url=getattr(self.config, 'OPENAI_API_URL', None),
                default_input_max_characters=getattr(self.config, 'INPUT_DAFAULT_MAX_CHARACTERS', 1000),
                default_generation_max_output_tokens=getattr(self.config, 'GENERATION_DAFAULT_MAX_TOKENS', 1000),
                default_generation_temperature=getattr(self.config, 'GENERATION_DAFAULT_TEMPERATURE', 0.1)
            )
            
        elif provider == LLMEnums.OLLAMA.value:
            from .LLM_Providers import OllamaProvider
            instance = OllamaProvider(
                api_url=getattr(self.config, 'OLLAMA_API_URL', 'http://localhost:11434'),
                default_input_max_characters=getattr(self.config, 'INPUT_DAFAULT_MAX_CHARACTERS', 1000),
                default_generation_max_output_tokens=getattr(self.config, 'GENERATION_DAFAULT_MAX_TOKENS', 1000),
                default_generation_temperature=getattr(self.config, 'GENERATION_DAFAULT_TEMPERATURE', 0.1)
            )

        elif provider == LLMEnums.GEMINI.value:
            from .LLM_Providers import GeminiProvider
            instance = GeminiProvider(
                api_key=getattr(self.config, 'GEMINI_API_KEY', None),
                api_url=getattr(self.config, 'GEMINI_API_URL', None),
                default_input_max_characters=getattr(self.config, 'INPUT_DAFAULT_MAX_CHARACTERS', 1000),
                default_generation_max_output_tokens=getattr(self.config, 'GENERATION_DAFAULT_MAX_TOKENS', 1000),
                default_generation_temperature=getattr(self.config, 'GENERATION_DAFAULT_TEMPERATURE', 0.1)
            )

        elif provider == LLMEnums.COHERE.value:
            from ..providers.CoHereProvider import CoHereProvider
            instance = CoHereProvider(
                api_key=getattr(self.config, 'COHERE_API_KEY', None),
                api_url=getattr(self.config, 'COHERE_API_URL', None),
                default_input_max_characters=getattr(self.config, 'INPUT_DAFAULT_MAX_CHARACTERS', 1000),
                default_generation_max_output_tokens=getattr(self.config, 'GENERATION_DAFAULT_MAX_TOKENS', 1000),
                default_generation_temperature=getattr(self.config, 'GENERATION_DAFAULT_TEMPERATURE', 0.1)
            )

        if instance:
            # Inject model IDs from global config
            gen_model = getattr(self.config, 'GENERATION_MODEL_ID', None)
            if gen_model:
                # If we configured a model from another provider, don't override the default
                if provider == LLMEnums.COHERE.value and any(x in gen_model.lower() for x in ["gpt", "gemini", "claude"]):
                    pass
                elif provider == LLMEnums.OPENAI.value and any(x in gen_model.lower() for x in ["command", "gemini", "claude"]):
                    pass
                elif provider == LLMEnums.GEMINI.value and any(x in gen_model.lower() for x in ["gpt", "command", "claude"]):
                    pass
                else:
                    instance.set_generation_model(gen_model)

            embed_model = getattr(self.config, 'EMBEDDING_MODEL_ID', None)
            if embed_model:
                if provider == LLMEnums.COHERE.value and "text-embedding" in embed_model.lower():
                    pass
                elif provider == LLMEnums.OPENAI.value and "embed" in embed_model.lower():
                    pass
                else:
                    instance.set_embedding_model(embed_model)
            return instance

        # Return None if the provider is not supported
        return None
