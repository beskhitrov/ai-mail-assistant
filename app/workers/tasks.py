"""RQ tasks for background email analysis."""

from typing import Any

from app.db.session import SessionLocal
from app.repositories.email_repository import EmailRepository
from app.schemas.email import EmailCreate
from app.services.email_analyzer import EmailAnalyzer
from app.services.llm_factory import create_llm_client


def analyze_email_job(email_data: dict[str, Any]) -> dict[str, Any]:
    """Analyze email in background, save result, and return serialized response."""
    email = EmailCreate.model_validate(email_data)
    analyzer = EmailAnalyzer(create_llm_client())
    response = analyzer.analyze(email)

    db = SessionLocal()
    try:
        EmailRepository(db).save_email_with_analysis(email, response.analysis)
    finally:
        db.close()

    return response.model_dump(mode="json")
