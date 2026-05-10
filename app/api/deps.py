"""FastAPI dependencies."""

from collections.abc import Generator

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.services.llm_client import LLMClient
from app.services.llm_factory import LLMClientConfigurationError, create_llm_client


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for API handlers."""
    yield from get_db_session()


def get_llm_client() -> LLMClient:
    """Return configured LLM client for email analysis."""
    try:
        return create_llm_client()
    except LLMClientConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LLM client is not configured",
        ) from exc
