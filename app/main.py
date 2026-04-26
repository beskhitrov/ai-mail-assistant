"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.api.routes.emails import router as emails_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    application = FastAPI(title=settings.app_name)
    application.include_router(health_router)
    application.include_router(emails_router)
    return application


app = create_app()
