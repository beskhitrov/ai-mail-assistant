"""Tests for email API endpoints."""

from collections.abc import Generator
from typing import Any

from fastapi.testclient import TestClient

from app.api.deps import get_db
from app.db.models import Email
from app.main import app


class FakeSession:
    """Fake DB session for API tests."""

    def add(self, model: Any) -> None:
        """Assign id to email model before analysis is created."""
        if isinstance(model, Email):
            model.id = 1

    def flush(self) -> None:
        """No-op flush."""

    def commit(self) -> None:
        """No-op commit."""

    def rollback(self) -> None:
        """No-op rollback."""

    def refresh(self, model: Any) -> None:
        """No-op refresh."""


def override_get_db() -> Generator[FakeSession, None, None]:
    """Return fake session for API tests."""
    yield FakeSession()


def test_analyze_email_endpoint_returns_analysis() -> None:
    """POST /api/v1/emails/analyze should analyze and save email."""
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    response = client.post(
        "/api/v1/emails/analyze",
        json={
            "sender": "teacher@example.com",
            "recipient": "student@example.com",
            "subject": "Срочно подготовить отчет",
            "body": "Нужно подготовить отчет по проекту.",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 201
    data = response.json()
    assert data["analysis"]["priority"] == "high"
    assert data["analysis"]["category"] == "work"
    assert data["analysis"]["tasks"][0]["title"] == "Нужно подготовить отчет по проекту"
