from __future__ import annotations

from app.config import settings
from app.providers.base import ReportProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.groq_provider import GroqProvider

_SUPPORTED_PROVIDERS = {"groq", "gemini"}


def get_report_provider(provider_name: str | None = None) -> ReportProvider | None:
    """
    Return a configured report provider, or None when no API key is available.

    Default provider is Groq (`REPORT_PROVIDER=groq`).
    """
    name = (provider_name or settings.report_provider).strip().lower()
    if name not in _SUPPORTED_PROVIDERS:
        name = "groq"

    if name == "gemini":
        if settings.gemini_api_key:
            return GeminiProvider()
        return None

    if settings.groq_api_key:
        return GroqProvider()
    return None
