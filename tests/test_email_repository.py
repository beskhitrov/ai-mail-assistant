"""Tests for email repository."""

from typing import Any

from app.db.models import Email, EmailAnalysis
from app.repositories.email_repository import EmailRepository
from app.schemas.email import EmailAnalysisResult, EmailCategory, EmailCreate, Priority


class FakeSession:
    """Small fake session for repository unit tests."""

    def __init__(self) -> None:
        """Initialize fake session state."""
        self.added: list[Any] = []
        self.committed = False
        self.rolled_back = False

    def add(self, model: Any) -> None:
        """Store added models."""
        self.added.append(model)

    def flush(self) -> None:
        """Simulate database id assignment."""
        for model in self.added:
            if isinstance(model, Email):
                model.id = 1

    def commit(self) -> None:
        """Mark transaction as committed."""
        self.committed = True

    def rollback(self) -> None:
        """Mark transaction as rolled back."""
        self.rolled_back = True

    def refresh(self, model: Any) -> None:
        """No-op refresh for fake session."""


def test_repository_saves_email_and_analysis() -> None:
    """Repository should create both ORM models and commit transaction."""
    session = FakeSession()
    email = EmailCreate(
        sender="teacher@example.com",
        recipient="student@example.com",
        subject="Project report",
        body="Please prepare the project report.",
    )
    analysis = EmailAnalysisResult(
        summary="Project report: Please prepare the project report.",
        category=EmailCategory.WORK,
        priority=Priority.MEDIUM,
        tasks=[],
    )

    saved_email, saved_analysis = EmailRepository(session).save_email_with_analysis(
        email,
        analysis,
    )

    assert session.committed is True
    assert session.rolled_back is False
    assert saved_email.sender == "teacher@example.com"
    assert saved_analysis.email_id == 1
    assert isinstance(session.added[0], Email)
    assert isinstance(session.added[1], EmailAnalysis)
