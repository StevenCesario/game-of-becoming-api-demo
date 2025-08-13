from abc import ABC, abstractmethod
from typing import Dict, Any
from pydantic import BaseModel

class BaseLLMProvider(ABC):
    """
    Abstract Base Class for LLM providers.
    This is our "Universal Remote" contract.
    Any AI provider we use MUST implement these methods.
    """

    @abstractmethod
    def generate_structured_response(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: BaseModel
    ) -> Dict[str, Any]:
        """
        Takes prompts and a Pydantic model, and returns a dictionary
        that conforms to that model's structure.
        """
        pass