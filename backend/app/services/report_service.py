"""
Report generation service with BYOK support and prompt export mode.

Architecture:
  Report Service -> AI Provider Interface -> Groq / OpenAI / Gemini / Anthropic / OpenRouter

Payload limits:
  - REPORT_TOP_FINDINGS_LIMIT (default 15)
  - REPORT_MAX_PAYLOAD_BYTES (default 12_000)
  - Top duplicate findings capped at 5
  - Only structured findings sent — never source code
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from app.config import settings
from app.logging_config import get_logger
from app.providers.base import ReportProviderError
from app.providers.factory import AiConfig, get_report_provider
from app.summary import build_findings_by_category

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a senior software architect writing a professional repository audit report.

You will receive structured analysis data containing metrics, scores, category breakdowns, and findings from automated static analysis tools.

Rules:
- Base your report ONLY on the provided data.
- Do NOT invent issues not present in the findings.
- Do NOT request or assume access to source code.
- Write in clear, professional markdown.
- Include these sections exactly:
  1. Executive Summary
  2. Security Assessment
  3. Maintainability Assessment
  4. Dead Code Assessment
  5. Duplicate Logic Assessment
  6. Architecture Assessment
  7. Architectural Risks
  8. Refactoring Roadmap
  9. Priority Actions
- Reference specific finding IDs or messages when discussing issues.
- Be concise but actionable.
"""

_REPORT_FINDING_FIELDS = (
    "id",
    "type",
    "severity",
    "category",
    "file",
    "line",
    "message",
    "confidence",
    "file_a",
    "function_a",
    "file_b",
    "function_b",
    "similarity",
)

AI_UNAVAILABLE_HEADER = "# AI report unavailable.\n"


@dataclass(frozen=True)
class ReportResult:
    ai_report: str
    prompt_export: str | None


def _trim_finding(finding: dict) -> dict:
    trimmed = {key: finding[key] for key in _REPORT_FINDING_FIELDS if key in finding}
    if finding.get("type") == "duplicate_logic" and "evidence" in finding:
        evidence = finding["evidence"]
        for key in ("file_a", "function_a", "file_b", "function_b", "similarity"):
            if key in evidence and key not in trimmed:
                trimmed[key] = evidence[key]
    return trimmed


def _build_report_payload(
    metrics: dict,
    scores: dict,
    top_findings: list[dict],
    findings_count: int,
    *,
    findings_limit: int,
) -> dict:
    return {
        "metrics": {
            "files_scanned": metrics.get("files_scanned"),
            "total_lines": metrics.get("total_lines"),
            "python_files": metrics.get("python_files"),
            "javascript_files": metrics.get("javascript_files"),
            "typescript_files": metrics.get("typescript_files"),
            "findings_count": findings_count,
            "findings_by_category": metrics.get("findings_by_category", {}),
            "dead_code_summary": metrics.get("dead_code_summary", {}),
            "duplicate_logic_summary": metrics.get("duplicate_logic_summary", {}),
            "architecture_summary": metrics.get("architecture_summary", {}),
            "dependency_summary": metrics.get("dependency_summary", {}),
        },
        "scores": scores,
        "top_findings": [_trim_finding(f) for f in top_findings[:findings_limit]],
        "top_duplicate_findings": [
            _trim_finding(f)
            for f in top_findings
            if f.get("type") == "duplicate_logic"
        ][:5],
        "top_architecture_findings": [
            _trim_finding(f)
            for f in top_findings
            if f.get("category") == "architecture"
        ][:8],
    }


def _payload_size(payload: dict) -> int:
    return len(json.dumps(payload, separators=(",", ":")))


def _build_size_limited_payload(
    metrics: dict,
    scores: dict,
    top_findings: list[dict],
    findings_count: int,
) -> tuple[dict, int]:
    limit = settings.report_top_findings_limit
    while limit >= 1:
        payload = _build_report_payload(
            metrics,
            scores,
            top_findings,
            findings_count,
            findings_limit=limit,
        )
        size = _payload_size(payload)
        if size <= settings.report_max_payload_bytes:
            return payload, size
        limit -= 1

    payload = _build_report_payload(metrics, scores, [], findings_count, findings_limit=0)
    return payload, _payload_size(payload)


def build_prompt_export(
    metrics: dict,
    scores: dict,
    findings: list[dict],
    top: list[dict],
) -> str:
    payload, payload_bytes = _build_size_limited_payload(metrics, scores, top, len(findings))
    return (
        "You are a senior software architect. Generate a professional repository audit report "
        "from the structured analysis data below.\n\n"
        "Include these sections:\n"
        "1. Executive Summary\n"
        "2. Security Assessment\n"
        "3. Maintainability Assessment\n"
        "4. Dead Code Assessment\n"
        "5. Duplicate Logic Assessment\n"
        "6. Architecture Assessment\n"
        "7. Architectural Risks\n"
        "8. Refactoring Roadmap\n"
        "9. Priority Actions\n\n"
        "Rules:\n"
        "- Use ONLY the data provided.\n"
        "- Do NOT invent issues.\n"
        "- Do NOT request source code.\n"
        "- Write in clear markdown.\n\n"
        f"Payload size: {payload_bytes} bytes\n\n"
        f"```json\n{json.dumps(payload, indent=2)}\n```"
    )


def generate_report(
    metrics: dict,
    scores: dict,
    findings: list[dict],
    top: list[dict] | None = None,
    ai_config: AiConfig | None = None,
) -> ReportResult:
    trimmed_top = (top or [])[: settings.report_top_findings_limit]
    provider = get_report_provider(ai_config)

    if provider is None:
        logger.info("No AI provider configured; returning prompt export")
        return ReportResult(
            ai_report="",
            prompt_export=build_prompt_export(metrics, scores, findings, trimmed_top),
        )

    payload, payload_bytes = _build_size_limited_payload(
        metrics,
        scores,
        trimmed_top,
        len(findings),
    )

    logger.info(
        "%s payload prepared: %d bytes (limit %d), %d top findings (total findings: %d)",
        provider.name.title(),
        payload_bytes,
        settings.report_max_payload_bytes,
        len(payload["top_findings"]),
        len(findings),
    )

    user_prompt = (
        "Generate a professional software audit report based on the following "
        "structured analysis results:\n\n"
        f"```json\n{json.dumps(payload, indent=2)}\n```"
    )

    try:
        report = provider.generate(SYSTEM_PROMPT, user_prompt)
        return ReportResult(ai_report=report, prompt_export=None)
    except ReportProviderError as exc:
        logger.warning("%s report generation failed: %s", provider.name.title(), exc)
        return ReportResult(
            ai_report=AI_UNAVAILABLE_HEADER.strip(),
            prompt_export=build_prompt_export(metrics, scores, findings, trimmed_top),
        )
    except Exception:
        logger.exception("%s report generation failed unexpectedly", provider.name.title())
        return ReportResult(
            ai_report=AI_UNAVAILABLE_HEADER.strip(),
            prompt_export=build_prompt_export(metrics, scores, findings, trimmed_top),
        )


def verify_ai_connection(ai_config: AiConfig) -> tuple[str, str]:
    """Test provider connectivity. Returns (status, message). Never logs API keys."""
    provider = get_report_provider(ai_config)
    if provider is None:
        return "invalid", "API key is required."

    try:
        provider.generate(
            "You are a connectivity test assistant.",
            "Reply with exactly: connected",
        )
        return "connected", "Connection successful."
    except ReportProviderError as exc:
        message = str(exc).lower()
        if "invalid" in message or "401" in message:
            return "invalid", "Invalid API key."
        if "rate limit" in message:
            return "error", "Rate limit exceeded. Try again later."
        return "error", str(exc)
    except Exception:
        logger.exception("AI connection test failed")
        return "error", "Provider error. Check model and API key."
