"""Telegram bot business service."""

from typing import Any

from app.repositories.email_repository import EmailRepository
from app.schemas.email import EmailAnalysisResponse, EmailCreate
from app.services.email_analyzer import EmailAnalyzer
from app.services.llm_client import LLMClient
from app.services.llm_factory import create_llm_client


def build_email_from_telegram_text(text: str, telegram_id: int) -> EmailCreate:
    """Build EmailCreate schema from Telegram message text."""
    return EmailCreate(
        sender=f"telegram-{telegram_id}@telegram.local",
        recipient="assistant@ai-mail-assistant.local",
        subject=_build_subject(text),
        body=text.strip(),
    )


def analyze_telegram_email(
    text: str,
    telegram_id: int,
    db_session: Any | None = None,
    llm_client: LLMClient | None = None,
) -> EmailAnalysisResponse:
    """Analyze Telegram message as email and optionally save result."""
    email = build_email_from_telegram_text(text, telegram_id)
    analyzer = EmailAnalyzer(llm_client or create_llm_client())
    response = analyzer.analyze(email)

    if db_session is not None:
        EmailRepository(db_session).save_email_with_analysis(email, response.analysis)

    return response


def _build_subject(text: str) -> str:
    """Build compact subject from Telegram message text."""
    first_line = text.strip().splitlines()[0]
    subject = first_line[:80].strip()
    return subject or "Telegram email"
