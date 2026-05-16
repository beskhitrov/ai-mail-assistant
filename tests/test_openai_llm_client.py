"""Tests for OpenAI-compatible LLM client."""

import json

import httpx
import pytest

from app.schemas.email import EmailCreate
from app.services.llm_client import (
    LLMClientError,
    LLMResponseError,
    OpenAICompatibleLLMClient,
)


def test_openai_compatible_client_parses_valid_response() -> None:
    """Client should parse provider JSON into EmailAnalysisResult."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://example.test/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-key"
        return httpx.Response(
            status_code=200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "summary": "Нужно подготовить отчет.",
                                    "category": "work",
                                    "priority": "high",
                                    "tasks": [
                                        {
                                            "title": "Подготовить отчет",
                                            "deadline": "2026-05-10",
                                            "assignee": "user",
                                            "priority": "high",
                                        },
                                    ],
                                    "entities": {
                                        "people": [],
                                        "organizations": [],
                                        "dates": ["2026-05-10"],
                                    },
                                    "draft_reply": "Здравствуйте! Подготовлю отчет.",
                                },
                            ),
                        },
                    },
                ],
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = OpenAICompatibleLLMClient(
        api_key="test-key",
        model="test-model",
        base_url="https://example.test/v1",
        http_client=http_client,
    )
    email = EmailCreate(
        sender="teacher@example.com",
        recipient="student@example.com",
        subject="Отчет",
        body="Нужно подготовить отчет.",
    )

    result = client.analyze_email(email)

    assert result.summary == "Нужно подготовить отчет."
    assert result.category == "work"
    assert result.priority == "high"
    assert result.tasks[0].title == "Подготовить отчет"


def test_openai_compatible_client_rejects_invalid_json_response() -> None:
    """Client should raise domain error for invalid provider content."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": "not json"}}]},
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = OpenAICompatibleLLMClient(
        api_key="test-key",
        model="test-model",
        base_url="https://example.test/v1",
        http_client=http_client,
    )
    email = EmailCreate(
        sender="teacher@example.com",
        recipient="student@example.com",
        subject="Отчет",
        body="Нужно подготовить отчет.",
    )

    with pytest.raises(LLMResponseError):
        client.analyze_email(email)


def test_openai_compatible_client_raises_error_for_http_failure() -> None:
    """Client should raise domain error when provider returns HTTP error."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=401, json={"error": "invalid key"})

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = OpenAICompatibleLLMClient(
        api_key="test-key",
        model="test-model",
        base_url="https://example.test/v1",
        http_client=http_client,
    )
    email = EmailCreate(
        sender="teacher@example.com",
        recipient="student@example.com",
        subject="Отчет",
        body="Нужно подготовить отчет.",
    )

    with pytest.raises(LLMClientError, match="HTTP 401"):
        client.analyze_email(email)
