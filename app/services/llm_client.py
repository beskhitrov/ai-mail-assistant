"""LLM client abstractions and fake implementation for local development."""

from typing import Protocol

from app.schemas.email import (
    EmailAnalysisResult,
    EmailCategory,
    EmailCreate,
    EmailEntities,
    Priority,
    TaskItem,
)


class LLMClient(Protocol):
    """Protocol for clients that can analyze an email."""

    def analyze_email(self, email: EmailCreate) -> EmailAnalysisResult:
        """Return structured analysis for an email."""


class FakeLLMClient:
    """Deterministic LLM client used before real API integration."""

    def analyze_email(self, email: EmailCreate) -> EmailAnalysisResult:
        """Build a predictable analysis result from email text."""
        text = f"{email.subject}\n{email.body}".lower()
        priority = self._detect_priority(text)
        category = self._detect_category(text)
        tasks = self._extract_tasks(email.body, priority)

        return EmailAnalysisResult(
            summary=self._build_summary(email),
            category=category,
            priority=priority,
            tasks=tasks,
            entities=EmailEntities(),
            draft_reply="Здравствуйте! Спасибо за письмо. Я изучу информацию и вернусь с ответом.",
        )

    @staticmethod
    def _detect_priority(text: str) -> Priority:
        """Detect priority by simple keywords suitable for MVP tests."""
        high_markers = ("срочно", "urgent", "asap", "важно")
        if any(marker in text for marker in high_markers):
            return Priority.HIGH
        return Priority.MEDIUM

    @staticmethod
    def _detect_category(text: str) -> EmailCategory:
        """Detect category by simple keywords."""
        work_markers = ("отчет", "проект", "задача", "meeting", "deadline")
        finance_markers = ("invoice", "счет", "оплата", "payment")

        if any(marker in text for marker in finance_markers):
            return EmailCategory.FINANCE
        if any(marker in text for marker in work_markers):
            return EmailCategory.WORK
        return EmailCategory.OTHER

    @staticmethod
    def _extract_tasks(body: str, priority: Priority) -> list[TaskItem]:
        """Extract a minimal task list from the email body."""
        task_markers = ("нужно", "надо", "please", "подготовить")
        lower_body = body.lower()

        if not any(marker in lower_body for marker in task_markers):
            return []

        first_sentence = body.split(".")[0].strip()
        title = first_sentence if first_sentence else "Обработать письмо"
        return [TaskItem(title=title, priority=priority)]

    @staticmethod
    def _build_summary(email: EmailCreate) -> str:
        """Build a short deterministic summary."""
        body_preview = email.body.strip().splitlines()[0][:120]
        return f"{email.subject}: {body_preview}"
