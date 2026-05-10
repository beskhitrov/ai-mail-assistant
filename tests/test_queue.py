"""Tests for queue helpers."""

from app.schemas.email import EmailCreate
from app.core.queue import enqueue_email_analysis


class FakeJob:
    """Fake RQ job returned by queue.enqueue."""

    id = "job-123"


class FakeQueue:
    """Fake RQ queue for unit tests."""

    def __init__(self) -> None:
        """Initialize fake queue state."""
        self.enqueued_function: str | None = None
        self.enqueued_payload: dict[str, object] | None = None

    def enqueue(self, function_path: str, payload: dict[str, object]) -> FakeJob:
        """Store enqueue call and return fake job."""
        self.enqueued_function = function_path
        self.enqueued_payload = payload
        return FakeJob()


def test_enqueue_email_analysis_returns_job_id() -> None:
    """Queue helper should enqueue serialized email and return job id."""
    queue = FakeQueue()
    email = EmailCreate(
        sender="teacher@example.com",
        recipient="student@example.com",
        subject="Project report",
        body="Please prepare the project report.",
    )

    job_id = enqueue_email_analysis(email, queue)

    assert job_id == "job-123"
    assert queue.enqueued_function == "app.workers.tasks.analyze_email_job"
    assert queue.enqueued_payload == email.model_dump(mode="json")
