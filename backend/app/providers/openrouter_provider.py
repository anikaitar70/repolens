from __future__ import annotations

from app.providers.openai_compatible import OpenAICompatibleProvider

OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterProvider(OpenAICompatibleProvider):
    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: float | None = None,
    ) -> None:
        super().__init__(
            provider_name="openrouter",
            api_url=OPENROUTER_CHAT_URL,
            api_key=api_key,
            model=model,
            timeout_seconds=timeout_seconds,
            extra_headers={
                "HTTP-Referer": "https://repolens.local",
                "X-Title": "RepoLens",
            },
        )
