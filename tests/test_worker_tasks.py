"""Tests for background worker tasks."""

from typing import Any

from app.workers import tasks


class FakeSession:
    """Fake database session used by worker tests."""

    closed = False

    def close(self) -> None:
        """Mark session as closed."""
        self.closed = True


class FakeRepository:
    """Fake repository for worker task tests."""

    saved: tuple[Any, Any] | None = None

    def __init__(self, session: FakeSession) -> None:
        """Store fake session."""
        self.session = session

    def save_email_with_analysis(self, email: Any, analysis: Any) -> tuple[Any, Any]:
        """Store saved email and analysis."""
        self.saved = (email, analysis)
        return email, analysis


def test_analyze_email_job_uses_service_and_repository(monkeypatch: Any) -> None:
    """Worker task should analyze email and persist analysis."""
    session = FakeSession()
    repository = FakeRepository(session)

    monkeypatch.setattr(tasks, "SessionLocal", lambda: session)
    monkeypatch.setattr(tasks, "EmailRepository", lambda db: repository)

    result = tasks.analyze_email_job(
        {
            "sender": "teacher@example.com",
            "recipient": "student@example.com",
            "subject": "Срочно подготовить отчет",
            "body": "Нужно подготовить отчет по проекту.",
        },
    )

    assert result["analysis"]["priority"] == "high"
    assert result["analysis"]["category"] == "work"
    assert repository.saved is not None
    assert session.closed is True
