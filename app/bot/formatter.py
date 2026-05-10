"""Format email analysis results for Telegram messages."""

from app.schemas.email import EmailAnalysisResponse, TaskItem


def format_analysis_for_telegram(response: EmailAnalysisResponse) -> str:
    """Format structured analysis result for Telegram user."""
    analysis = response.analysis
    lines = [
        "Анализ письма",
        "",
        f"Summary: {analysis.summary}",
        f"Category: {analysis.category}",
        f"Priority: {analysis.priority}",
        "",
        "Tasks:",
        _format_tasks(analysis.tasks),
    ]

    if analysis.draft_reply:
        lines.extend(["", "Draft reply:", analysis.draft_reply])

    return "\n".join(lines)


def _format_tasks(tasks: list[TaskItem]) -> str:
    """Format extracted tasks for Telegram output."""
    if not tasks:
        return "Нет задач."

    return "\n".join(f"- {task.title}" for task in tasks)
