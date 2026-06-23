from __future__ import annotations

import httpx

from app.config import settings
from app.logging_config import get_logger
from app.providers.base import ReportProvider, ReportProviderError

logger = get_logger(__name__)

ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"


class AnthropicProvider(ReportProvider):
    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: float | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout_seconds if timeout_seconds is not None else settings.report_timeout_seconds

    @property
    def name(self) -> str:
        return "anthropic"

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self._api_key:
            raise ReportProviderError("Anthropic API key is not configured.")

        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        body = {
            "model": self._model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "temperature": 0.2,
        }

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(ANTHROPIC_MESSAGES_URL, headers=headers, json=body)
        except httpx.TimeoutException as exc:
            raise ReportProviderError("Anthropic request timed out.", retryable=True) from exc
        except httpx.RequestError as exc:
            raise ReportProviderError(f"Anthropic network error: {exc}") from exc

        if response.status_code == 401:
            raise ReportProviderError("Anthropic API key is invalid.")
        if response.status_code == 429:
            raise ReportProviderError("Anthropic rate limit exceeded.", retryable=True)
        if response.status_code >= 500:
            raise ReportProviderError(
                f"Anthropic service error ({response.status_code}).",
                retryable=True,
            )
        if response.status_code >= 400:
            raise ReportProviderError(f"Anthropic request failed ({response.status_code}).")

        try:
            payload = response.json()
            blocks = payload["content"]
            text = "".join(block.get("text", "") for block in blocks if block.get("type") == "text")
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("Invalid Anthropic response payload: %s", response.text[:500])
            raise ReportProviderError("Anthropic returned an invalid response.") from exc

        text = text.strip()
        if not text:
            raise ReportProviderError("Anthropic returned an empty report.")

        logger.info("Anthropic report generated (model=%s)", self._model)
        return text
