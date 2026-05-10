"""Email analysis endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_llm_client
from app.repositories.email_repository import EmailRepository, RepositoryError
from app.schemas.email import EmailAnalysisResponse, EmailCreate
from app.services.email_analyzer import EmailAnalyzer
from app.services.llm_client import LLMClient

router = APIRouter(prefix="/api/v1/emails", tags=["emails"])


@router.post(
    "/analyze",
    response_model=EmailAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
def analyze_email(
    email: EmailCreate,
    db: Annotated[Session, Depends(get_db)],
    llm_client: Annotated[LLMClient, Depends(get_llm_client)],
) -> EmailAnalysisResponse:
    """Analyze email, save input and analysis, then return structured result."""
    analyzer = EmailAnalyzer(llm_client)
    response = analyzer.analyze(email)

    try:
        EmailRepository(db).save_email_with_analysis(email, response.analysis)
    except RepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save email analysis",
        ) from exc

    return response
