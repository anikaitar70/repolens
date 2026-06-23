from __future__ import annotations

from dataclasses import dataclass

from app.config import settings
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.base import ReportProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.groq_provider import GroqProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.openrouter_provider import OpenRouterProvider

SUPPORTED_PROVIDERS = {"groq", "openai", "gemini", "anthropic", "openrouter"}

DEFAULT_MODELS: dict[str, str] = {
    "groq": "llama-3.3-70b-versatile",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.0-flash",
    "anthropic": "claude-3-5-sonnet-20241022",
    "openrouter": "llama-3.3-70b-versatile",
}


@dataclass(frozen=True)
class AiConfig:
    provider: str | None = None
    model: str | None = None
    api_key: str | None = None


def resolve_model(provider: str, model: str | None) -> str:
    if model and model.strip():
        return model.strip()
    return DEFAULT_MODELS.get(provider, DEFAULT_MODELS["groq"])


def _resolve_api_key(provider: str, byok_key: str | None) -> str | None:
    if byok_key and byok_key.strip():
        return byok_key.strip()

    if provider == "groq" and settings.groq_api_key:
        return settings.groq_api_key
    if provider == "gemini" and settings.gemini_api_key:
        return settings.gemini_api_key
    return None


def get_report_provider(ai_config: AiConfig | None = None) -> ReportProvider | None:
    """
    Return a report provider from BYOK config or server env fallback.

    BYOK keys are used only for the current request and never persisted.
    """
    provider_name = (ai_config.provider if ai_config and ai_config.provider else settings.report_provider)
    provider_name = provider_name.strip().lower()
    if provider_name not in SUPPORTED_PROVIDERS:
        provider_name = "groq"

    api_key = _resolve_api_key(provider_name, ai_config.api_key if ai_config else None)
    if not api_key:
        return None

    model = resolve_model(provider_name, ai_config.model if ai_config else None)

    if provider_name == "groq":
        return GroqProvider(api_key=api_key, model=model)
    if provider_name == "openai":
        return OpenAIProvider(api_key=api_key, model=model)
    if provider_name == "gemini":
        return GeminiProvider(api_key=api_key, model=model)
    if provider_name == "anthropic":
        return AnthropicProvider(api_key=api_key, model=model)
    if provider_name == "openrouter":
        return OpenRouterProvider(api_key=api_key, model=model)

    return None
