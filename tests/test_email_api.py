"""Tests for email API endpoints."""

from collections.abc import Generator
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import get_db, get_llm_client, get_queue
from app.db.models import Email, EmailAnalysis
from app.main import app
from app.schemas.email import EmailAnalysisResult, EmailCreate
from app.services.llm_client import LLMClientError


class FakeSession:
    """Fake DB session for API tests."""

    def __init__(self, fail_on_commit: bool = False) -> None:
        """Initialize fake session."""
        self.fail_on_commit = fail_on_commit
        self.emails = [build_stored_email()]

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

    def execute(self, statement: Any) -> Any:
        """Return fake stored emails for history endpoints."""
        statement_text = str(statement)
        if "WHERE emails.id" not in statement_text:
            return FakeExecuteResult(self.emails)
        params = statement.compile().params
        email_id = next(iter(params.values()), None)
        emails = [email for email in self.emails if email.id == email_id]
        return FakeExecuteResult(emails)


class FakeScalarResult:
    """Fake SQLAlchemy scalar result."""

    def __init__(self, emails: list[Email]) -> None:
        """Initialize fake scalar result."""
        self._emails = emails

    def all(self) -> list[Email]:
        """Return all fake emails."""
        return self._emails

    def first(self) -> Email | None:
        """Return first fake email."""
        return self._emails[0] if self._emails else None


class FakeExecuteResult:
    """Fake SQLAlchemy execute result."""

    def __init__(self, emails: list[Email]) -> None:
        """Initialize fake execute result."""
        self._emails = emails

    def scalars(self) -> FakeScalarResult:
        """Return fake scalar result."""
        return FakeScalarResult(self._emails)


def build_stored_email() -> Email:
    """Build stored email ORM object for API tests."""
    created_at = datetime(2026, 5, 10, tzinfo=timezone.utc)
    email = Email(
        id=1,
        sender="teacher@example.com",
        recipient="student@example.com",
        subject="Project report",
        body="Please prepare the project report.",
        received_at=None,
        created_at=created_at,
    )
    email.analysis = EmailAnalysis(
        id=1,
        email_id=1,
        summary="Project report summary",
        category="work",
        priority="medium",
        tasks=[],
        entities={"people": [], "organizations": [], "dates": []},
        draft_reply="Thank you.",
        created_at=created_at,
    )
    return email


def override_get_db() -> Generator[FakeSession, None, None]:
    """Return fake session for API tests."""
    yield FakeSession()


def override_failing_get_db() -> Generator[FakeSession, None, None]:
    """Return fake session that fails on commit."""
    yield FakeSession(fail_on_commit=True)


class FailingLLMClient:
    """Fake LLM client that simulates provider failure."""

    def analyze_email(self, email: EmailCreate) -> EmailAnalysisResult:
        """Raise provider error instead of returning analysis."""
        raise LLMClientError("provider is unavailable")


def override_failing_llm_client() -> FailingLLMClient:
    """Return failing LLM client for API tests."""
    return FailingLLMClient()


class FakeJob:
    """Fake queue job."""

    id = "job-123"


class FakeQueue:
    """Fake queue for async API tests."""

    def __init__(self) -> None:
        """Initialize fake queue state."""
        self.job_result: dict[str, Any] | None = None

    def enqueue(self, function_path: str, payload: dict[str, object]) -> FakeJob:
        """Return fake job id for enqueue call."""
        return FakeJob()

    def fetch_job(self, job_id: str) -> Any | None:
        """Return fake job by id."""
        if job_id != "job-123":
            return None
        return FakeStatusJob(self.job_result)


class FakeStatusJob:
    """Fake RQ job for API status tests."""

    id = "job-123"
    exc_info = None

    def __init__(self, result: dict[str, Any] | None = None) -> None:
        """Initialize fake job result."""
        self.result = result

    def get_status(self, refresh: bool = True) -> str:
        """Return fake status."""
        if self.result is None:
            return "queued"
        return "finished"


fake_queue = FakeQueue()


def override_get_queue() -> FakeQueue:
    """Return fake queue for API tests."""
    return fake_queue


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


def test_analyze_email_endpoint_returns_502_when_llm_fails(
    client: TestClient,
) -> None:
    """Endpoint should return bad gateway when LLM provider fails."""
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_llm_client] = override_failing_llm_client

    response = client.post(
        "/api/v1/emails/analyze",
        json={
            "sender": "teacher@example.com",
            "recipient": "student@example.com",
            "subject": "Project report",
            "body": "Please prepare the project report.",
        },
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "LLM provider failed to analyze email"}


def test_list_email_history_endpoint_returns_items(client: TestClient) -> None:
    """GET /api/v1/emails should return stored analysis history."""
    app.dependency_overrides[get_db] = override_get_db

    response = client.get("/api/v1/emails")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["email"]["id"] == 1
    assert data[0]["email"]["subject"] == "Project report"
    assert data[0]["analysis"]["summary"] == "Project report summary"


def test_get_email_history_item_endpoint_returns_item(client: TestClient) -> None:
    """GET /api/v1/emails/{email_id} should return one stored item."""
    app.dependency_overrides[get_db] = override_get_db

    response = client.get("/api/v1/emails/1")

    assert response.status_code == 200
    data = response.json()
    assert data["email"]["id"] == 1
    assert data["analysis"]["category"] == "work"


def test_get_email_history_item_endpoint_returns_404(client: TestClient) -> None:
    """GET /api/v1/emails/{email_id} should return 404 for missing item."""
    app.dependency_overrides[get_db] = override_get_db

    response = client.get("/api/v1/emails/100")

    assert response.status_code == 404
    assert response.json() == {"detail": "Email analysis history item not found"}


def test_analyze_email_async_endpoint_returns_job_id(client: TestClient) -> None:
    """POST /api/v1/emails/analyze-async should enqueue analysis job."""
    app.dependency_overrides[get_queue] = override_get_queue

    response = client.post(
        "/api/v1/emails/analyze-async",
        json={
            "sender": "teacher@example.com",
            "recipient": "student@example.com",
            "subject": "Project report",
            "body": "Please prepare the project report.",
        },
    )

    assert response.status_code == 202
    assert response.json() == {"job_id": "job-123", "status": "queued"}


def test_get_analysis_job_endpoint_returns_status(client: TestClient) -> None:
    """GET /api/v1/jobs/{job_id} should return queued job status."""
    fake_queue.job_result = None
    app.dependency_overrides[get_queue] = override_get_queue

    response = client.get("/api/v1/jobs/job-123")

    assert response.status_code == 200
    assert response.json() == {
        "job_id": "job-123",
        "status": "queued",
        "result": None,
        "error": None,
    }


def test_get_analysis_job_endpoint_returns_404_for_missing_job(
    client: TestClient,
) -> None:
    """GET /api/v1/jobs/{job_id} should return 404 for unknown job."""
    app.dependency_overrides[get_queue] = override_get_queue

    response = client.get("/api/v1/jobs/missing-job")

    assert response.status_code == 404
    assert response.json() == {"detail": "Analysis job not found"}
