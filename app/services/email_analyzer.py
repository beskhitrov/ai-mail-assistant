"""Business service for email analysis."""

from app.schemas.email import EmailAnalysisResponse, EmailCreate
from app.services.llm_client import FakeLLMClient, LLMClient


class EmailAnalyzer:
    """Analyze incoming emails using an injected LLM client."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        """Initialize analyzer with fake LLM by default."""
        self._llm_client = llm_client or FakeLLMClient()

    def analyze(self, email: EmailCreate) -> EmailAnalysisResponse:
        """Analyze email and return structured response."""
        analysis = self._llm_client.analyze_email(email)
        return EmailAnalysisResponse(email=email, analysis=analysis)
