"""Email analysis endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_llm_client, get_queue
from app.core.queue import (
    QueueOperationError,
    enqueue_email_analysis,
    get_email_analysis_job_status,
)
from app.db.models import Email, EmailAnalysis
from app.repositories.email_repository import EmailRepository, RepositoryError
from app.schemas.email import (
    EmailAnalysisRead,
    EmailAnalysisResponse,
    EmailCreate,
    EmailHistoryItem,
    EmailRead,
)
from app.schemas.job import JobCreateResponse, JobStatusResponse
from app.services.email_analyzer import EmailAnalyzer
from app.services.llm_client import LLMClient, LLMClientError

router = APIRouter(tags=["emails"])


@router.post(
    "/api/v1/emails/analyze",
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

    try:
        response = analyzer.analyze(email)
    except LLMClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM provider failed to analyze email",
        ) from exc

    try:
        EmailRepository(db).save_email_with_analysis(email, response.analysis)
    except RepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save email analysis",
        ) from exc

    return response


@router.get(
    "/api/v1/emails",
    response_model=list[EmailHistoryItem],
)
def list_email_history(
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[EmailHistoryItem]:
    """Return stored email analysis history."""
    try:
        emails = EmailRepository(db).list_emails_with_analysis(limit, offset)
    except RepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not list email analysis history",
        ) from exc

    return [_build_history_item(email) for email in emails]


@router.get(
    "/api/v1/emails/{email_id}",
    response_model=EmailHistoryItem,
)
def get_email_history_item(
    email_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> EmailHistoryItem:
    """Return one stored email and its analysis."""
    try:
        email = EmailRepository(db).get_email_with_analysis(email_id)
    except RepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not get email analysis history item",
        ) from exc

    if email is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email analysis history item not found",
        )

    return _build_history_item(email)


@router.post(
    "/api/v1/emails/analyze-async",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def analyze_email_async(
    email: EmailCreate,
    queue: Annotated[Any, Depends(get_queue)],
) -> JobCreateResponse:
    """Put email analysis into background queue and return job id."""
    try:
        job_id = enqueue_email_analysis(email, queue)
    except QueueOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not enqueue email analysis job",
        ) from exc

    return JobCreateResponse(job_id=job_id)


@router.get(
    "/api/v1/jobs/{job_id}",
    response_model=JobStatusResponse,
)
def get_analysis_job(
    job_id: str,
    queue: Annotated[Any, Depends(get_queue)],
) -> JobStatusResponse:
    """Return status and result for background email analysis job."""
    try:
        job_status = get_email_analysis_job_status(job_id, queue)
    except QueueOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not fetch email analysis job",
        ) from exc

    if job_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis job not found",
        )

    return JobStatusResponse.model_validate(job_status)


def _build_history_item(email: Email) -> EmailHistoryItem:
    """Build API schema from stored email ORM model."""
    return EmailHistoryItem(
        email=EmailRead(
            id=email.id,
            sender=email.sender,
            recipient=email.recipient,
            subject=email.subject,
            body=email.body,
            received_at=email.received_at,
            created_at=email.created_at,
        ),
        analysis=_build_analysis_read(email.analysis),
    )


def _build_analysis_read(analysis: EmailAnalysis | None) -> EmailAnalysisRead | None:
    """Build API schema from stored analysis ORM model."""
    if analysis is None:
        return None

    return EmailAnalysisRead.model_validate(
        {
            "id": analysis.id,
            "email_id": analysis.email_id,
            "summary": analysis.summary,
            "category": analysis.category,
            "priority": analysis.priority,
            "tasks": analysis.tasks,
            "entities": analysis.entities,
            "draft_reply": analysis.draft_reply,
            "created_at": analysis.created_at,
        },
    )
