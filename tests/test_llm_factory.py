"""Tests for LLM client factory."""

import pytest

from app.core.config import Settings
from app.services.llm_client import FakeLLMClient
from app.services.llm_factory import LLMClientConfigurationError, create_llm_client


def test_create_llm_client_returns_fake_client_by_default() -> None:
    """Factory should return fake client for local deterministic analysis."""
    settings = Settings(llm_provider="fake")

    client = create_llm_client(settings)

    assert isinstance(client, FakeLLMClient)


def test_create_llm_client_rejects_openai_until_client_is_implemented() -> None:
    """OpenAI provider should fail clearly until feature9 adds real client."""
    settings = Settings(llm_provider="openai", openai_api_key="test-key")

    with pytest.raises(LLMClientConfigurationError, match="feature9"):
        create_llm_client(settings)
