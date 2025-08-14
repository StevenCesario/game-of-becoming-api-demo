import os
from functools import lru_cache
from .base import BaseLLMProvider
from .anthropic_provider import AnthropicProvider

@lru_cache(maxsize=1)
def get_llm_provider() -> BaseLLMProvider:
    """
    Acts as a factory and a singleton to provide the configured LLM provider.

    This function reads the LLM_PROVIDER from environment variables and returns
    the appropriate provider instance. The `@lru_cache(maxsize=1)` decorator
    ensures that the provider is only initialized once per application lifecycle,
    making it highly efficient.

    Raises:
        ValueError: If the API key for the selected provider is not set,
                    or if the provider itself is unsupported.

    Returns:
        An instance of a class that inherits from BaseLLMProvider.
    """
    provider_name = os.getenv("LLM_PROVIDER", "anthropic").lower()

    if provider_name == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set.")
        return AnthropicProvider(api_key=api_key)
    
    # We can easily add other providers here in the future, e.g.:
    # if provider_name == "openai":
    #     return OpenAIProvider(...)
    
    raise ValueError(f"Unsupported LLM provider: {provider_name}")
