"""Pydantic schemas for background jobs."""

from pydantic import BaseModel, Field

from app.schemas.email import EmailAnalysisResponse


class JobCreateResponse(BaseModel):
    """Response returned after putting an email analysis into queue."""

    job_id: str = Field(..., min_length=1)
    status: str = "queued"


class JobStatusResponse(BaseModel):
    """Current status of background email analysis job."""

    job_id: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    result: EmailAnalysisResponse | None = None
    error: str | None = None
