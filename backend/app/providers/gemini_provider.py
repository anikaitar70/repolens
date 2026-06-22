from __future__ import annotations

import google.generativeai as genai

from app.config import settings
from app.logging_config import get_logger
from app.providers.base import ReportProvider, ReportProviderError

logger = get_logger(__name__)


class GeminiProvider(ReportProvider):
    """Legacy Gemini provider for optional backward compatibility."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else settings.gemini_api_key
        self._model = model if model is not None else settings.gemini_model

    @property
    def name(self) -> str:
        return "gemini"

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self._api_key:
            raise ReportProviderError("Gemini API key is not configured.")

        try:
            genai.configure(api_key=self._api_key)
            model = genai.GenerativeModel(
                model_name=self._model,
                system_instruction=system_prompt,
            )
            response = model.generate_content(user_prompt)
        except Exception as exc:
            message = str(exc).lower()
            if "resource_exhausted" in message or "429" in message:
                raise ReportProviderError("Gemini rate limit exceeded.", retryable=True) from exc
            raise ReportProviderError(f"Gemini report generation failed: {exc}") from exc

        text = (response.text or "").strip()
        if not text:
            raise ReportProviderError("Gemini returned an empty report.")

        logger.info("Gemini report generated successfully (model=%s)", self._model)
        return text
