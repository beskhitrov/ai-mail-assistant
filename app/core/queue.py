"""Queue helpers for background email analysis jobs."""

from importlib import import_module
from typing import Any

from app.core.config import Settings, get_settings
from app.schemas.email import EmailCreate


class QueueConfigurationError(Exception):
    """Raised when Redis/RQ queue dependencies are not available."""


class QueueOperationError(Exception):
    """Raised when queue operation fails."""


def get_redis_connection(settings: Settings | None = None) -> Any:
    """Create Redis connection from application settings."""
    current_settings = settings or get_settings()

    try:
        redis_module = import_module("redis")
    except ImportError as exc:
        msg = "redis package is required for background queues"
        raise QueueConfigurationError(msg) from exc

    return redis_module.Redis.from_url(current_settings.redis_url)


def get_analysis_queue(settings: Settings | None = None) -> Any:
    """Create RQ queue for email analysis jobs."""
    current_settings = settings or get_settings()

    try:
        rq_module = import_module("rq")
    except ImportError as exc:
        msg = "rq package is required for background queues"
        raise QueueConfigurationError(msg) from exc

    return rq_module.Queue(
        current_settings.analysis_queue_name,
        connection=get_redis_connection(current_settings),
    )


def enqueue_email_analysis(email: EmailCreate, queue: Any | None = None) -> str:
    """Enqueue email analysis job and return queue job id."""
    analysis_queue = queue or get_analysis_queue()
    try:
        job = analysis_queue.enqueue(
            "app.workers.tasks.analyze_email_job",
            email.model_dump(mode="json"),
        )
    except Exception as exc:
        msg = "Could not enqueue email analysis job"
        raise QueueOperationError(msg) from exc

    return str(job.id)


def get_email_analysis_job_status(
    job_id: str,
    queue: Any | None = None,
) -> dict[str, Any] | None:
    """Return serialized queue job status by id."""
    analysis_queue = queue or get_analysis_queue()

    try:
        job = analysis_queue.fetch_job(job_id)
    except Exception as exc:
        msg = "Could not fetch email analysis job"
        raise QueueOperationError(msg) from exc

    if job is None:
        return None

    status = job.get_status(refresh=True)
    status_value = getattr(status, "value", status)
    result = _get_job_result(job) if status_value == "finished" else None
    error = getattr(job, "exc_info", None) if status_value == "failed" else None

    return {
        "job_id": str(job.id),
        "status": str(status_value),
        "result": result,
        "error": error,
    }


def _get_job_result(job: Any) -> Any:
    """Read RQ job result across supported RQ versions."""
    if hasattr(job, "return_value"):
        return job.return_value(refresh=True)
    return getattr(job, "result", None)
