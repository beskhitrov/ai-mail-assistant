"""Tests for health endpoint handler."""

from app.api.routes.health import health_check


def test_health_check_returns_ok() -> None:
    """Health handler should confirm that the service is running."""
    assert health_check() == {"status": "ok"}
