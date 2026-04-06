from src.core.config import get_settings
from src.core.mock_provider import MockProvider


def build_provider():
    settings = get_settings()
    provider_name = settings.default_provider.lower()

    if provider_name == "openai":
        from src.core.openai_provider import OpenAIProvider

        return OpenAIProvider(model_name=settings.default_model, api_key=settings.openai_api_key)
    if provider_name in {"google", "gemini"}:
        from src.core.gemini_provider import GeminiProvider

        return GeminiProvider(model_name=settings.default_model, api_key=settings.gemini_api_key)
    if provider_name == "local":
        from src.core.local_provider import LocalProvider

        return LocalProvider(model_path=settings.local_model_path)
    return MockProvider(model_name=settings.default_model)
