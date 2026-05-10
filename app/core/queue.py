"""Queue helpers for background email analysis jobs."""

from importlib import import_module
from typing import Any

from app.core.config import Settings, get_settings
from app.schemas.email import EmailCreate


class QueueConfigurationError(Exception):
    """Raised when Redis/RQ queue dependencies are not available."""


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
    job = analysis_queue.enqueue(
        "app.workers.tasks.analyze_email_job",
        email.model_dump(mode="json"),
    )
    return str(job.id)
