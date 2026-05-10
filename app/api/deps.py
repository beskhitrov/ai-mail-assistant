"""FastAPI dependencies."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.services.llm_client import LLMClient
from app.services.llm_factory import create_llm_client


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for API handlers."""
    yield from get_db_session()


def get_llm_client() -> LLMClient:
    """Return configured LLM client for email analysis."""
    return create_llm_client()
