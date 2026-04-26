"""Tests for email API endpoints."""

from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import get_db
from app.db.models import Email
from app.main import app


class FakeSession:
    """Fake DB session for API tests."""

    def __init__(self, fail_on_commit: bool = False) -> None:
        """Initialize fake session."""
        self.fail_on_commit = fail_on_commit

    def add(self, model: Any) -> None:
        """Assign id to email model before analysis is created."""
        if isinstance(model, Email):
            model.id = 1

    def flush(self) -> None:
        """No-op flush."""

    def commit(self) -> None:
        """No-op commit."""
        if self.fail_on_commit:
            raise SQLAlchemyError("database is unavailable")

    def rollback(self) -> None:
        """No-op rollback."""

    def refresh(self, model: Any) -> None:
        """No-op refresh."""


def override_get_db() -> Generator[FakeSession, None, None]:
    """Return fake session for API tests."""
    yield FakeSession()


def override_failing_get_db() -> Generator[FakeSession, None, None]:
    """Return fake session that fails on commit."""
    yield FakeSession(fail_on_commit=True)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Return API test client and clean dependency overrides."""
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_analyze_email_endpoint_returns_analysis(client: TestClient) -> None:
    """POST /api/v1/emails/analyze should analyze and save email."""
    app.dependency_overrides[get_db] = override_get_db

    response = client.post(
        "/api/v1/emails/analyze",
        json={
            "sender": "teacher@example.com",
            "recipient": "student@example.com",
            "subject": "Срочно подготовить отчет",
            "body": "Нужно подготовить отчет по проекту.",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["analysis"]["priority"] == "high"
    assert data["analysis"]["category"] == "work"
    assert data["analysis"]["tasks"][0]["title"] == "Нужно подготовить отчет по проекту"


def test_analyze_email_endpoint_validates_payload(client: TestClient) -> None:
    """Endpoint should reject invalid email payload before business logic."""
    response = client.post(
        "/api/v1/emails/analyze",
        json={
            "sender": "invalid",
            "recipient": "student@example.com",
            "subject": "",
            "body": "Нужно подготовить отчет.",
        },
    )

    assert response.status_code == 422


def test_analyze_email_endpoint_returns_500_when_save_fails(
    client: TestClient,
) -> None:
    """Endpoint should return clear server error when repository fails."""
    app.dependency_overrides[get_db] = override_failing_get_db

    response = client.post(
        "/api/v1/emails/analyze",
        json={
            "sender": "teacher@example.com",
            "recipient": "student@example.com",
            "subject": "Project report",
            "body": "Please prepare the project report.",
        },
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Could not save email analysis"}
