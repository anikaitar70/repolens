import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.providers.base import ReportProviderError
from app.providers.factory import AiConfig, get_report_provider
from app.providers.groq_provider import GroqProvider
from app.services.report_service import (
    _build_size_limited_payload,
    generate_report,
)


@pytest.fixture
def sample_metrics() -> dict:
    return {
        "files_scanned": 3,
        "total_lines": 120,
        "python_files": 2,
        "javascript_files": 1,
        "typescript_files": 0,
        "findings_by_category": {"security": 1},
        "dead_code_summary": {"unused_imports": 1, "unused_variables": 0, "unused_functions": 0},
        "duplicate_logic_summary": {
            "duplicate_pairs": 0,
            "high_confidence_duplicates": 0,
            "medium_confidence_duplicates": 0,
            "possible_duplicates": 0,
        },
        "architecture_summary": {},
        "dependency_summary": {},
    }


@pytest.fixture
def sample_scores() -> dict:
    return {
        "maintainability": 90,
        "security": 80,
        "architecture": 95,
        "dead_code": 99,
        "architecture_risk": 95,
    }


@pytest.fixture
def sample_findings() -> list[dict]:
    return [
        {
            "id": "finding_1",
            "type": "security",
            "severity": "high",
            "category": "security",
            "file": "app.py",
            "line": 10,
            "message": "Hardcoded secret detected",
        }
    ]


def test_get_report_provider_missing_key():
    with patch("app.providers.factory.settings") as mock_settings:
        mock_settings.report_provider = "groq"
        mock_settings.groq_api_key = ""
        mock_settings.gemini_api_key = ""
        assert get_report_provider() is None
        assert get_report_provider(AiConfig(provider="groq", api_key="")) is None


def test_get_report_provider_groq():
    provider = get_report_provider(
        AiConfig(provider="groq", model="llama-3.3-70b-versatile", api_key="test-key")
    )
    assert provider is not None
    assert provider.name == "groq"


def test_generate_report_missing_api_key(sample_metrics, sample_scores, sample_findings):
    with patch("app.services.report_service.get_report_provider", return_value=None):
        result = generate_report(sample_metrics, sample_scores, sample_findings)
    assert result.ai_report == ""
    assert result.prompt_export is not None
    assert "Executive Summary" in result.prompt_export


def test_generate_report_success(sample_metrics, sample_scores, sample_findings):
    provider = MagicMock()
    provider.name = "groq"
    provider.generate.return_value = "# AI Report\n\n## Executive Summary\nAll good."

    with patch("app.services.report_service.get_report_provider", return_value=provider):
        result = generate_report(sample_metrics, sample_scores, sample_findings)

    assert result.ai_report.startswith("# AI Report")
    assert result.prompt_export is None
    provider.generate.assert_called_once()


def test_generate_report_rate_limit_fallback(sample_metrics, sample_scores, sample_findings):
    provider = MagicMock()
    provider.name = "groq"
    provider.generate.side_effect = ReportProviderError("Groq rate limit exceeded.", retryable=True)

    with patch("app.services.report_service.get_report_provider", return_value=provider):
        result = generate_report(sample_metrics, sample_scores, sample_findings)

    assert "AI report unavailable" in result.ai_report
    assert result.prompt_export is not None


def test_generate_report_invalid_key_fallback(sample_metrics, sample_scores, sample_findings):
    provider = MagicMock()
    provider.name = "groq"
    provider.generate.side_effect = ReportProviderError("Groq API key is invalid.")

    with patch("app.services.report_service.get_report_provider", return_value=provider):
        result = generate_report(sample_metrics, sample_scores, sample_findings)

    assert "AI report unavailable" in result.ai_report


def test_generate_report_empty_findings(sample_metrics, sample_scores):
    provider = MagicMock()
    provider.name = "groq"
    provider.generate.return_value = "# Empty Repo\n\nNo issues."

    with patch("app.services.report_service.get_report_provider", return_value=provider):
        result = generate_report(sample_metrics, sample_scores, [])

    assert result.ai_report.startswith("# Empty Repo")


def test_payload_size_limit_trims_findings(sample_metrics, sample_scores):
    findings = [
        {
            "id": f"finding_{index}",
            "type": "security",
            "severity": "high",
            "category": "security",
            "file": f"file_{index}.py",
            "line": index,
            "message": "x" * 500,
        }
        for index in range(30)
    ]

    with patch("app.services.report_service.settings") as mock_settings:
        mock_settings.report_top_findings_limit = 30
        mock_settings.report_max_payload_bytes = 2_000
        payload, size = _build_size_limited_payload(
            sample_metrics,
            sample_scores,
            findings,
            len(findings),
        )

    assert size <= 2_000
    assert len(payload["top_findings"]) < 30


def test_groq_provider_success():
    provider = GroqProvider(api_key="test-key", model="llama-3.3-70b-versatile", timeout_seconds=5.0)
    response = httpx.Response(
        200,
        json={"choices": [{"message": {"content": "# Groq Report"}}]},
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
    )

    with patch("httpx.Client.post", return_value=response):
        text = provider.generate("system", "user")

    assert text == "# Groq Report"


def test_groq_provider_invalid_key():
    provider = GroqProvider(api_key="bad-key", model="llama-3.3-70b-versatile", timeout_seconds=5.0)
    response = httpx.Response(
        401,
        json={"error": {"message": "invalid"}},
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
    )

    with patch("httpx.Client.post", return_value=response):
        with pytest.raises(ReportProviderError, match="invalid"):
            provider.generate("system", "user")


def test_groq_provider_rate_limit():
    provider = GroqProvider(api_key="test-key", model="llama-3.3-70b-versatile", timeout_seconds=5.0)
    response = httpx.Response(
        429,
        json={"error": {"message": "rate limit"}},
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
    )

    with patch("httpx.Client.post", return_value=response):
        with pytest.raises(ReportProviderError, match="rate limit"):
            provider.generate("system", "user")


def test_groq_provider_timeout():
    provider = GroqProvider(api_key="test-key", model="llama-3.3-70b-versatile", timeout_seconds=0.1)

    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("timed out")):
        with pytest.raises(ReportProviderError, match="timed out"):
            provider.generate("system", "user")


def test_groq_provider_network_error():
    provider = GroqProvider(api_key="test-key", model="llama-3.3-70b-versatile", timeout_seconds=5.0)

    with patch("httpx.Client.post", side_effect=httpx.ConnectError("connection failed")):
        with pytest.raises(ReportProviderError, match="network error"):
            provider.generate("system", "user")


def test_groq_provider_invalid_response():
    provider = GroqProvider(api_key="test-key", model="llama-3.3-70b-versatile", timeout_seconds=5.0)
    response = httpx.Response(
        200,
        json={"unexpected": "shape"},
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
    )

    with patch("httpx.Client.post", return_value=response):
        with pytest.raises(ReportProviderError, match="invalid response"):
            provider.generate("system", "user")


def test_payload_excludes_source_code(sample_metrics, sample_scores):
    findings = [
        {
            "id": "finding_1",
            "type": "security",
            "severity": "high",
            "category": "security",
            "file": "app.py",
            "line": 1,
            "message": "Issue found",
            "source": "def secret(): pass",
            "evidence": {"raw_code": "password = '123'"},
        }
    ]

    payload, _ = _build_size_limited_payload(sample_metrics, sample_scores, findings, 1)
    serialized = json.dumps(payload)

    assert "password" not in serialized
    assert "def secret" not in serialized
    assert "raw_code" not in serialized
