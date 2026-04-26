"""FastAPI dependencies."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import get_db_session


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for API handlers."""
    yield from get_db_session()
