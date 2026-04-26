"""Pydantic schemas for incoming emails and analysis results."""

from datetime import date, datetime
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field, field_validator


class EmailCategory(StrEnum):
    """Supported email categories."""

    WORK = "work"
    PERSONAL = "personal"
    FINANCE = "finance"
    SPAM = "spam"
    OTHER = "other"


class Priority(StrEnum):
    """Supported priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EmailCreate(BaseModel):
    """Input data required to analyze an email."""

    sender: str = Field(..., min_length=3, max_length=255)
    recipient: str = Field(..., min_length=3, max_length=255)
    subject: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)
    received_at: datetime | None = None

    @field_validator("sender", "recipient")
    @classmethod
    def validate_email_like_value(cls, value: str) -> str:
        """Validate email-like fields without adding extra dependencies."""
        if "@" not in value:
            msg = "must contain @"
            raise ValueError(msg)
        return value


class TaskItem(BaseModel):
    """Task extracted from an email."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    deadline: date | None = None
    assignee: str | None = Field(default=None, max_length=255)
    priority: Priority = Priority.MEDIUM

    model_config = ConfigDict(use_enum_values=True)


class EmailEntities(BaseModel):
    """Important entities extracted from an email."""

    people: list[str] = Field(default_factory=list)
    organizations: list[str] = Field(default_factory=list)
    dates: list[str] = Field(default_factory=list)


class EmailAnalysisResult(BaseModel):
    """Structured result returned by an LLM client."""

    summary: str = Field(..., min_length=1)
    category: EmailCategory
    priority: Priority
    tasks: list[TaskItem] = Field(default_factory=list)
    entities: EmailEntities = Field(default_factory=EmailEntities)
    draft_reply: str | None = None

    model_config = ConfigDict(use_enum_values=True)


class EmailAnalysisResponse(BaseModel):
    """Response returned by the analysis service."""

    email: EmailCreate
    analysis: EmailAnalysisResult
