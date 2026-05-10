"""Tests for email repository."""

from datetime import datetime, timezone
from typing import Any

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.db.models import Email, EmailAnalysis
from app.repositories.email_repository import EmailRepository, RepositoryError
from app.schemas.email import EmailAnalysisResult, EmailCategory, EmailCreate, Priority


class FakeSession:
    """Small fake session for repository unit tests."""

    def __init__(self, fail_on_commit: bool = False) -> None:
        """Initialize fake session state."""
        self.added: list[Any] = []
        self.committed = False
        self.rolled_back = False
        self.fail_on_commit = fail_on_commit

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
        if self.fail_on_commit:
            raise SQLAlchemyError("database is unavailable")
        self.committed = True

    def rollback(self) -> None:
        """Mark transaction as rolled back."""
        self.rolled_back = True

    def refresh(self, model: Any) -> None:
        """No-op refresh for fake session."""

    def execute(self, statement: Any) -> Any:
        """No-op execute for write-only tests."""
        raise SQLAlchemyError("unexpected execute")


class FakeScalarResult:
    """Fake SQLAlchemy scalar result."""

    def __init__(self, emails: list[Email]) -> None:
        """Initialize fake result with emails."""
        self._emails = emails

    def all(self) -> list[Email]:
        """Return all fake emails."""
        return self._emails

    def first(self) -> Email | None:
        """Return first fake email."""
        return self._emails[0] if self._emails else None


class FakeExecuteResult:
    """Fake SQLAlchemy execute result."""

    def __init__(self, emails: list[Email]) -> None:
        """Initialize fake execute result."""
        self._emails = emails

    def scalars(self) -> FakeScalarResult:
        """Return fake scalar result."""
        return FakeScalarResult(self._emails)


class FakeReadSession(FakeSession):
    """Fake session for repository read methods."""

    def __init__(self, emails: list[Email]) -> None:
        """Initialize fake session with stored emails."""
        super().__init__()
        self._emails = emails

    def execute(self, statement: Any) -> FakeExecuteResult:
        """Return fake emails, filtering by id when statement has id param."""
        statement_text = str(statement)
        if "WHERE emails.id" not in statement_text:
            return FakeExecuteResult(self._emails)
        params = statement.compile().params
        email_id = next(iter(params.values()), None)
        return FakeExecuteResult([email for email in self._emails if email.id == email_id])


def build_stored_email(email_id: int = 1) -> Email:
    """Build stored email ORM object for repository tests."""
    created_at = datetime(2026, 5, 10, tzinfo=timezone.utc)
    email = Email(
        id=email_id,
        sender="teacher@example.com",
        recipient="student@example.com",
        subject="Project report",
        body="Please prepare the project report.",
        received_at=None,
        created_at=created_at,
    )
    email.analysis = EmailAnalysis(
        id=1,
        email_id=email_id,
        summary="Project report summary",
        category="work",
        priority="medium",
        tasks=[],
        entities={"people": [], "organizations": [], "dates": []},
        draft_reply="Thank you.",
        created_at=created_at,
    )
    return email


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


def test_repository_rolls_back_when_commit_fails() -> None:
    """Repository should rollback and raise domain error on database failure."""
    session = FakeSession(fail_on_commit=True)
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

    with pytest.raises(RepositoryError):
        EmailRepository(session).save_email_with_analysis(email, analysis)

    assert session.committed is False
    assert session.rolled_back is True


def test_repository_lists_emails_with_analysis() -> None:
    """Repository should return stored email analysis history."""
    email = build_stored_email()
    session = FakeReadSession([email])

    result = EmailRepository(session).list_emails_with_analysis(limit=50, offset=0)

    assert result == [email]
    assert result[0].analysis is not None
    assert result[0].analysis.summary == "Project report summary"


def test_repository_gets_email_with_analysis_by_id() -> None:
    """Repository should return one stored email by id."""
    email = build_stored_email(email_id=42)
    session = FakeReadSession([email])

    result = EmailRepository(session).get_email_with_analysis(42)

    assert result == email


def test_repository_returns_none_when_email_is_missing() -> None:
    """Repository should return None when stored email does not exist."""
    session = FakeReadSession([build_stored_email(email_id=42)])

    result = EmailRepository(session).get_email_with_analysis(100)

    assert result is None
