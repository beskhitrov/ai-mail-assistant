"""Factory for selecting an LLM client implementation."""

from app.core.config import Settings, get_settings
from app.services.llm_client import FakeLLMClient, LLMClient


class LLMClientConfigurationError(Exception):
    """Raised when LLM client settings are invalid or unsupported."""


def create_llm_client(settings: Settings | None = None) -> LLMClient:
    """Create an LLM client according to application settings."""
    current_settings = settings or get_settings()

    if current_settings.llm_provider == "fake":
        return FakeLLMClient()

    if current_settings.llm_provider == "openai":
        msg = "OpenAI-compatible LLM client will be implemented in feature9"
        raise LLMClientConfigurationError(msg)

    msg = f"Unsupported LLM provider: {current_settings.llm_provider}"
    raise LLMClientConfigurationError(msg)
