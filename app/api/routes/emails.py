"""Email analysis endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_llm_client, get_queue
from app.core.queue import (
    QueueOperationError,
    enqueue_email_analysis,
    get_email_analysis_job_status,
)
from app.repositories.email_repository import EmailRepository, RepositoryError
from app.schemas.email import EmailAnalysisResponse, EmailCreate
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
