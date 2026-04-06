from typing import Any, Dict, Generator, Optional

from src.core.llm_provider import LLMProvider


class MockProvider(LLMProvider):
    """Deterministic provider for local development without external APIs."""

    def __init__(self, model_name: str = "mock-llm"):
        super().__init__(model_name=model_name, api_key=None)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        content = (
            "This is a mock provider response. "
            "Use FAQ lookup for v1 or tool orchestration for v2 in local development."
        )
        return {
            "content": content,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "latency_ms": 0,
            "provider": "mock",
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        yield self.generate(prompt, system_prompt)["content"]
