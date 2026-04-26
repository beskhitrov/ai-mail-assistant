"""Tests for SQLAlchemy database models."""

from app.db.models import Email, EmailAnalysis
from app.db.base import Base


def test_email_tables_are_registered_in_metadata() -> None:
    """ORM models should be present in SQLAlchemy metadata."""
    assert "emails" in Base.metadata.tables
    assert "email_analyses" in Base.metadata.tables


def test_email_analysis_relationship_is_configured() -> None:
    """Email and EmailAnalysis should be linked by relationship fields."""
    assert Email.analysis.property.back_populates == "email"
    assert EmailAnalysis.email.property.back_populates == "analysis"
