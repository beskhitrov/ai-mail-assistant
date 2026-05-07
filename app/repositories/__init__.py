"""Application repositories."""

from app.repositories.email_repository import EmailRepository, RepositoryError

__all__ = ["EmailRepository", "RepositoryError"]
