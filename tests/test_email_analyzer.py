"""Tests for email schemas and analyzer service."""

import pytest
from pydantic import ValidationError

from app.schemas.email import EmailAnalysisResult, EmailCategory, EmailCreate, Priority
from app.services.email_analyzer import EmailAnalyzer
from app.services.llm_client import FakeLLMClient


def test_email_create_validates_email_like_fields() -> None:
    """Email schema should reject invalid sender and recipient values."""
    with pytest.raises(ValidationError):
        EmailCreate(
            sender="invalid",
            recipient="user@example.com",
            subject="Sprint status",
            body="Please prepare report.",
        )


def test_fake_llm_client_returns_structured_analysis() -> None:
    """Fake LLM should return deterministic structured analysis."""
    email = EmailCreate(
        sender="teacher@example.com",
        recipient="student@example.com",
        subject="Срочно подготовить отчет",
        body="Нужно подготовить отчет по проекту до пятницы.",
    )

    result = FakeLLMClient().analyze_email(email)

    assert isinstance(result, EmailAnalysisResult)
    assert result.category == EmailCategory.WORK
    assert result.priority == Priority.HIGH
    assert result.tasks
    assert result.tasks[0].title == "Нужно подготовить отчет по проекту до пятницы"


def test_email_analyzer_uses_llm_client() -> None:
    """Analyzer service should combine input email with LLM analysis."""
    email = EmailCreate(
        sender="manager@example.com",
        recipient="student@example.com",
        subject="Project update",
        body="Please send the current project status.",
    )

    response = EmailAnalyzer().analyze(email)

    assert response.email == email
    assert response.analysis.summary.startswith("Project update:")
    assert response.analysis.tasks[0].priority == Priority.MEDIUM
