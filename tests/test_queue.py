"""Tests for queue helpers."""

from app.schemas.email import EmailCreate
from app.core.queue import enqueue_email_analysis, get_email_analysis_job_status


class FakeJob:
    """Fake RQ job returned by queue.enqueue."""

    id = "job-123"


class FakeQueue:
    """Fake RQ queue for unit tests."""

    def __init__(self) -> None:
        """Initialize fake queue state."""
        self.enqueued_function: str | None = None
        self.enqueued_payload: dict[str, object] | None = None
        self.job: FakeStatusJob | None = None

    def enqueue(self, function_path: str, payload: dict[str, object]) -> FakeJob:
        """Store enqueue call and return fake job."""
        self.enqueued_function = function_path
        self.enqueued_payload = payload
        return FakeJob()

    def fetch_job(self, job_id: str) -> "FakeStatusJob | None":
        """Return fake job by id."""
        if self.job is not None and self.job.id == job_id:
            return self.job
        return None


class FakeStatusJob:
    """Fake RQ job with status and result."""

    def __init__(self, status: str, result: dict[str, object] | None = None) -> None:
        """Initialize fake status job."""
        self.id = "job-123"
        self.status = status
        self.result = result
        self.exc_info = "traceback" if status == "failed" else None

    def get_status(self, refresh: bool = True) -> str:
        """Return fake job status."""
        return self.status


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


def test_get_email_analysis_job_status_returns_finished_result() -> None:
    """Queue helper should serialize finished job result."""
    queue = FakeQueue()
    queue.job = FakeStatusJob(
        status="finished",
        result={
            "email": {
                "sender": "teacher@example.com",
                "recipient": "student@example.com",
                "subject": "Project report",
                "body": "Please prepare the project report.",
                "received_at": None,
            },
            "analysis": {
                "summary": "Project report summary",
                "category": "work",
                "priority": "medium",
                "tasks": [],
                "entities": {"people": [], "organizations": [], "dates": []},
                "draft_reply": "Thank you.",
            },
        },
    )

    status = get_email_analysis_job_status("job-123", queue)

    assert status is not None
    assert status["job_id"] == "job-123"
    assert status["status"] == "finished"
    assert status["result"] == queue.job.result
    assert status["error"] is None


def test_get_email_analysis_job_status_returns_none_for_missing_job() -> None:
    """Queue helper should return None when job does not exist."""
    queue = FakeQueue()

    status = get_email_analysis_job_status("missing-job", queue)

    assert status is None
