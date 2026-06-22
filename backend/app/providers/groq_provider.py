from __future__ import annotations

import httpx

from app.config import settings
from app.logging_config import get_logger
from app.providers.base import ReportProvider, ReportProviderError

logger = get_logger(__name__)

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqProvider(ReportProvider):
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else settings.groq_api_key
        self._model = model if model is not None else settings.groq_model
        self._timeout = timeout_seconds if timeout_seconds is not None else settings.report_timeout_seconds

    @property
    def name(self) -> str:
        return "groq"

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self._api_key:
            raise ReportProviderError("Groq API key is not configured.")

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(GROQ_CHAT_URL, headers=headers, json=body)
        except httpx.TimeoutException as exc:
            raise ReportProviderError("Groq request timed out.", retryable=True) from exc
        except httpx.RequestError as exc:
            raise ReportProviderError(f"Groq network error: {exc}") from exc

        if response.status_code == 401:
            raise ReportProviderError("Groq API key is invalid.")
        if response.status_code == 429:
            raise ReportProviderError("Groq rate limit exceeded.", retryable=True)
        if response.status_code >= 500:
            raise ReportProviderError(
                f"Groq service error ({response.status_code}).",
                retryable=True,
            )
        if response.status_code >= 400:
            raise ReportProviderError(f"Groq request failed ({response.status_code}).")

        try:
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            logger.warning("Invalid Groq response payload: %s", response.text[:500])
            raise ReportProviderError("Groq returned an invalid response.") from exc

        text = str(content).strip()
        if not text:
            raise ReportProviderError("Groq returned an empty report.")

        logger.info("Groq report generated successfully (model=%s)", self._model)
        return text
