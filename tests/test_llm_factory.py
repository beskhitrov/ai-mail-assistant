"""Tests for LLM client factory."""

import pytest

from app.core.config import Settings
from app.services.llm_client import FakeLLMClient, OpenAICompatibleLLMClient
from app.services.llm_factory import LLMClientConfigurationError, create_llm_client


def test_create_llm_client_returns_fake_client_by_default() -> None:
    """Factory should return fake client for local deterministic analysis."""
    settings = Settings(llm_provider="fake")

    client = create_llm_client(settings)

    assert isinstance(client, FakeLLMClient)


def test_create_llm_client_returns_openai_client_when_api_key_is_configured() -> None:
    """Factory should create OpenAI-compatible client for openai provider."""
    settings = Settings(llm_provider="openai", openai_api_key="test-key")

    client = create_llm_client(settings)

    assert isinstance(client, OpenAICompatibleLLMClient)


def test_create_llm_client_rejects_openai_without_api_key() -> None:
    """OpenAI provider should require API key."""
    settings = Settings(llm_provider="openai", openai_api_key=None)

    with pytest.raises(LLMClientConfigurationError, match="OPENAI_API_KEY"):
        create_llm_client(settings)
