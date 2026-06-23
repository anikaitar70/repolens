from __future__ import annotations

import httpx

from app.config import settings
from app.logging_config import get_logger
from app.providers.base import ReportProvider, ReportProviderError

logger = get_logger(__name__)


class OpenAICompatibleProvider(ReportProvider):
    """Shared client for OpenAI-compatible chat completion APIs."""

    def __init__(
        self,
        *,
        provider_name: str,
        api_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self._provider_name = provider_name
        self._api_url = api_url
        self._api_key = api_key
        self._model = model
        self._timeout = timeout_seconds if timeout_seconds is not None else settings.report_timeout_seconds
        self._extra_headers = extra_headers or {}

    @property
    def name(self) -> str:
        return self._provider_name

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self._api_key:
            raise ReportProviderError(f"{self._provider_name.title()} API key is not configured.")

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            **self._extra_headers,
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
                response = client.post(self._api_url, headers=headers, json=body)
        except httpx.TimeoutException as exc:
            raise ReportProviderError(
                f"{self._provider_name.title()} request timed out.",
                retryable=True,
            ) from exc
        except httpx.RequestError as exc:
            raise ReportProviderError(
                f"{self._provider_name.title()} network error: {exc}"
            ) from exc

        if response.status_code == 401:
            raise ReportProviderError(f"{self._provider_name.title()} API key is invalid.")
        if response.status_code == 429:
            raise ReportProviderError(
                f"{self._provider_name.title()} rate limit exceeded.",
                retryable=True,
            )
        if response.status_code >= 500:
            raise ReportProviderError(
                f"{self._provider_name.title()} service error ({response.status_code}).",
                retryable=True,
            )
        if response.status_code >= 400:
            raise ReportProviderError(
                f"{self._provider_name.title()} request failed ({response.status_code})."
            )

        try:
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            logger.warning(
                "Invalid %s response payload: %s",
                self._provider_name,
                response.text[:500],
            )
            raise ReportProviderError(
                f"{self._provider_name.title()} returned an invalid response."
            ) from exc

        text = str(content).strip()
        if not text:
            raise ReportProviderError(f"{self._provider_name.title()} returned an empty report.")

        logger.info("%s report generated (model=%s)", self._provider_name.title(), self._model)
        return text
