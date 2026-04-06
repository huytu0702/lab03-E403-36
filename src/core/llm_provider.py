from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, Optional


class LLMProvider(ABC):
    """
    Abstract Base Class for LLM Providers.
    Supports OpenAI, Gemini, and Local models.
    """

    def __init__(self, model_name: str, api_key: Optional[str] = None, provider_name: str = "unknown"):
        self.model_name = model_name
        self.api_key = api_key
        self.provider_name = provider_name

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Produce a non-streaming completion.
        Returns:
            Dict containing:
            - content: The response text
            - usage: { 'prompt_tokens', 'completion_tokens', 'total_tokens' }
            - latency_ms: Response time
        """
        raise NotImplementedError

    @abstractmethod
    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        """Produce a streaming completion."""
        raise NotImplementedError
