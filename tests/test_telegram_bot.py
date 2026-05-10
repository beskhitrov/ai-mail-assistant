"""Tests for Telegram bot service and formatting."""

from typing import Any

from app.bot.formatter import format_analysis_for_telegram
from app.bot.service import analyze_telegram_email, build_email_from_telegram_text
from app.schemas.email import (
    EmailAnalysisResult,
    EmailCategory,
    EmailCreate,
    Priority,
    TaskItem,
)


class StaticLLMClient:
    """Fake LLM client for Telegram bot tests."""

    def analyze_email(self, email: EmailCreate) -> EmailAnalysisResult:
        """Return static analysis result."""
        return EmailAnalysisResult(
            summary="Нужно подготовить отчет.",
            category=EmailCategory.WORK,
            priority=Priority.HIGH,
            tasks=[TaskItem(title="Подготовить отчет", priority=Priority.HIGH)],
            draft_reply="Здравствуйте! Подготовлю отчет.",
        )


class FakeSession:
    """Fake DB session for Telegram bot service tests."""

    def __init__(self) -> None:
        """Initialize fake session state."""
        self.added: list[Any] = []
        self.committed = False

    def add(self, model: Any) -> None:
        """Store added model."""
        self.added.append(model)

    def flush(self) -> None:
        """Assign fake email id."""
        for model in self.added:
            if model.__class__.__name__ == "Email":
                model.id = 1

    def commit(self) -> None:
        """Mark transaction as committed."""
        self.committed = True

    def rollback(self) -> None:
        """No-op rollback."""

    def refresh(self, model: Any) -> None:
        """No-op refresh."""

    def execute(self, statement: Any) -> Any:
        """No-op execute."""


def test_build_email_from_telegram_text() -> None:
    """Telegram text should be converted to EmailCreate."""
    email = build_email_from_telegram_text(
        "Срочно подготовить отчет\nДо пятницы.",
        telegram_id=123,
    )

    assert email.sender == "telegram-123@telegram.local"
    assert email.recipient == "assistant@ai-mail-assistant.local"
    assert email.subject == "Срочно подготовить отчет"
    assert email.body == "Срочно подготовить отчет\nДо пятницы."


def test_analyze_telegram_email_saves_result_when_session_is_provided() -> None:
    """Telegram service should reuse analyzer and repository."""
    session = FakeSession()

    response = analyze_telegram_email(
        "Нужно подготовить отчет.",
        telegram_id=123,
        db_session=session,
        llm_client=StaticLLMClient(),
    )

    assert response.analysis.priority == Priority.HIGH
    assert response.analysis.tasks[0].title == "Подготовить отчет"
    assert session.committed is True


def test_format_analysis_for_telegram() -> None:
    """Formatter should include summary, tasks and draft reply."""
    response = analyze_telegram_email(
        "Нужно подготовить отчет.",
        telegram_id=123,
        llm_client=StaticLLMClient(),
    )

    text = format_analysis_for_telegram(response)

    assert "Summary: Нужно подготовить отчет." in text
    assert "- Подготовить отчет" in text
    assert "Draft reply:" in text
