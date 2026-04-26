"""Shared SQLAlchemy declarative base and model metadata."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""


from app.db.models import Email, EmailAnalysis  # noqa: E402, F401
