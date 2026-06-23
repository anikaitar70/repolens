from __future__ import annotations

from app.providers.openai_compatible import OpenAICompatibleProvider

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIProvider(OpenAICompatibleProvider):
    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: float | None = None,
    ) -> None:
        super().__init__(
            provider_name="openai",
            api_url=OPENAI_CHAT_URL,
            api_key=api_key,
            model=model,
            timeout_seconds=timeout_seconds,
        )
