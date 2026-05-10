"""Factory for selecting an LLM client implementation."""

from app.core.config import Settings, get_settings
from app.services.llm_client import FakeLLMClient, LLMClient, OpenAICompatibleLLMClient


class LLMClientConfigurationError(Exception):
    """Raised when LLM client settings are invalid or unsupported."""


def create_llm_client(settings: Settings | None = None) -> LLMClient:
    """Create an LLM client according to application settings."""
    current_settings = settings or get_settings()

    if current_settings.llm_provider == "fake":
        return FakeLLMClient()

    if current_settings.llm_provider == "openai":
        if not current_settings.openai_api_key:
            msg = "OPENAI_API_KEY is required when LLM_PROVIDER=openai"
            raise LLMClientConfigurationError(msg)

        return OpenAICompatibleLLMClient(
            api_key=current_settings.openai_api_key,
            model=current_settings.openai_model,
            base_url=current_settings.openai_base_url,
        )

    msg = f"Unsupported LLM provider: {current_settings.llm_provider}"
    raise LLMClientConfigurationError(msg)
