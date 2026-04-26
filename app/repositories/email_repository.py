"""Repository for storing emails and their analysis results."""

from typing import Any, Protocol

from sqlalchemy.exc import SQLAlchemyError

from app.db.models import Email, EmailAnalysis
from app.schemas.email import EmailAnalysisResult, EmailCreate


class DatabaseSession(Protocol):
    """Minimal session interface required by the repository."""

    def add(self, instance: Any) -> None:
        """Add ORM instance to the current transaction."""

    def flush(self) -> None:
        """Flush pending changes to assign generated values."""

    def commit(self) -> None:
        """Commit current transaction."""

    def rollback(self) -> None:
        """Rollback current transaction."""

    def refresh(self, instance: Any) -> None:
        """Refresh ORM instance from database state."""


class RepositoryError(Exception):
    """Raised when repository operation fails."""


class EmailRepository:
    """Persist emails and their analysis results."""

    def __init__(self, session: DatabaseSession) -> None:
        """Initialize repository with SQLAlchemy session."""
        self._session = session

    def save_email_with_analysis(
        self,
        email: EmailCreate,
        analysis: EmailAnalysisResult,
    ) -> tuple[Email, EmailAnalysis]:
        """Save email and analysis in one transaction."""
        email_model = Email(
            sender=email.sender,
            recipient=email.recipient,
            subject=email.subject,
            body=email.body,
            received_at=email.received_at,
        )

        try:
            self._session.add(email_model)
            self._session.flush()

            analysis_model = EmailAnalysis(
                email_id=email_model.id,
                summary=analysis.summary,
                category=str(analysis.category),
                priority=str(analysis.priority),
                tasks=[task.model_dump(mode="json") for task in analysis.tasks],
                entities=analysis.entities.model_dump(mode="json"),
                draft_reply=analysis.draft_reply,
            )

            self._session.add(analysis_model)
            self._session.commit()
            self._session.refresh(email_model)
            self._session.refresh(analysis_model)
        except SQLAlchemyError as exc:
            self._session.rollback()
            raise RepositoryError("Could not save email analysis") from exc

        return email_model, analysis_model
