"""LLM client abstractions and implementations."""

import json
from typing import Protocol

import httpx
from pydantic import ValidationError

from app.schemas.email import (
    EmailAnalysisResult,
    EmailCategory,
    EmailCreate,
    EmailEntities,
    Priority,
    TaskItem,
)


OPENAI_SYSTEM_PROMPT = """
Ты AI Mail Assistant. Проанализируй письмо и верни только валидный JSON.

Формат ответа:
{
  "summary": "краткое содержание письма",
  "category": "work|personal|finance|spam|other",
  "priority": "low|medium|high",
  "tasks": [
    {
      "title": "название задачи",
      "description": "детали задачи или null",
      "deadline": "YYYY-MM-DD или null",
      "assignee": "исполнитель или null",
      "priority": "low|medium|high"
    }
  ],
  "entities": {
    "people": [],
    "organizations": [],
    "dates": []
  },
  "draft_reply": "черновик ответа или null"
}
""".strip()


class LLMClient(Protocol):
    """Protocol for clients that can analyze an email."""

    def analyze_email(self, email: EmailCreate) -> EmailAnalysisResult:
        """Return structured analysis for an email."""


class LLMClientError(Exception):
    """Raised when an LLM provider request fails."""


class LLMResponseError(LLMClientError):
    """Raised when an LLM response cannot be parsed or validated."""


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


class OpenAICompatibleLLMClient:
    """LLM client for OpenAI Chat Completions-compatible APIs."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        http_client: httpx.Client | None = None,
        max_retries: int = 2,
    ) -> None:
        """Initialize OpenAI-compatible client."""
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._http_client = http_client or httpx.Client(timeout=30.0)
        self._max_retries = max_retries

    def analyze_email(self, email: EmailCreate) -> EmailAnalysisResult:
        """Analyze email through an OpenAI-compatible chat completions API."""
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": OPENAI_SYSTEM_PROMPT},
                {"role": "user", "content": self._build_user_prompt(email)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        response = self._post_with_retries(payload)
        return self._parse_analysis(response)

    @staticmethod
    def _build_user_prompt(email: EmailCreate) -> str:
        """Build prompt with email fields for the model."""
        return (
            "Проанализируй письмо.\n"
            f"Отправитель: {email.sender}\n"
            f"Получатель: {email.recipient}\n"
            f"Тема: {email.subject}\n"
            f"Дата получения: {email.received_at}\n"
            f"Текст письма:\n{email.body}"
        )

    def _post_with_retries(self, payload: dict[str, object]) -> dict[str, object]:
        """Send request and retry transient provider failures."""
        last_error: LLMClientError | None = None

        for attempt in range(self._max_retries + 1):
            try:
                response = self._http_client.post(
                    f"{self._base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    msg = "LLM provider returned non-object JSON"
                    raise LLMResponseError(msg)
                return data
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code < 500 or attempt == self._max_retries:
                    msg = f"LLM provider returned HTTP {exc.response.status_code}"
                    raise LLMClientError(msg) from exc
                last_error = LLMClientError("LLM provider temporary HTTP error")
            except httpx.RequestError as exc:
                if attempt == self._max_retries:
                    msg = "LLM provider request failed"
                    raise LLMClientError(msg) from exc
                last_error = LLMClientError("LLM provider temporary request error")

        msg = "LLM provider request failed after retries"
        raise last_error or LLMClientError(msg)

    @staticmethod
    def _parse_analysis(response: dict[str, object]) -> EmailAnalysisResult:
        """Parse OpenAI-compatible response into EmailAnalysisResult."""
        try:
            choices = response["choices"]
            if not isinstance(choices, list) or not choices:
                msg = "LLM response does not contain choices"
                raise LLMResponseError(msg)

            first_choice = choices[0]
            if not isinstance(first_choice, dict):
                msg = "LLM response choice has invalid format"
                raise LLMResponseError(msg)

            message = first_choice["message"]
            if not isinstance(message, dict):
                msg = "LLM response message has invalid format"
                raise LLMResponseError(msg)

            content = message["content"]
            if not isinstance(content, str):
                msg = "LLM response content is not text"
                raise LLMResponseError(msg)

            analysis_data = json.loads(content)
            return EmailAnalysisResult.model_validate(analysis_data)
        except (KeyError, json.JSONDecodeError, ValidationError) as exc:
            msg = "LLM response does not match expected analysis format"
            raise LLMResponseError(msg) from exc
