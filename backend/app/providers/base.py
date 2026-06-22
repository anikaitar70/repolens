from __future__ import annotations

from abc import ABC, abstractmethod


class ReportProviderError(Exception):
    """Raised when an AI report provider cannot generate a report."""

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class ReportProvider(ABC):
    """Interface for AI report-generation backends."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g. groq, gemini)."""

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate markdown report text from structured prompts."""
