"""
Report generation service.

Architecture:
  Report Service -> AI Provider Interface -> Groq / Gemini providers

Payload limits (documented in README):
  - REPORT_TOP_FINDINGS_LIMIT: max findings sent to the AI provider (default 15)
  - REPORT_MAX_PAYLOAD_BYTES: hard cap on JSON payload size (default 12_000)
  - Top duplicate findings capped at 5
  - Only structured fields are sent — never source code or raw files
"""

from __future__ import annotations

import json

from app.config import settings
from app.logging_config import get_logger
from app.providers.base import ReportProviderError
from app.providers.factory import get_report_provider
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
  7. Prioritized Refactoring Plan
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
        },
        "scores": scores,
        "top_findings": [_trim_finding(f) for f in top_findings[:findings_limit]],
        "top_duplicate_findings": [
            _trim_finding(f)
            for f in top_findings
            if f.get("type") == "duplicate_logic"
        ][:5],
    }


def _payload_size(payload: dict) -> int:
    return len(json.dumps(payload, separators=(",", ":")))


def _build_size_limited_payload(
    metrics: dict,
    scores: dict,
    top_findings: list[dict],
    findings_count: int,
) -> tuple[dict, int]:
    """
    Build a payload within REPORT_MAX_PAYLOAD_BYTES by reducing top findings count.
    """
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

    payload = _build_report_payload(
        metrics,
        scores,
        [],
        findings_count,
        findings_limit=0,
    )
    return payload, _payload_size(payload)


def generate_report(
    metrics: dict,
    scores: dict,
    findings: list[dict],
    top: list[dict] | None = None,
) -> str:
    trimmed_top = (top or [])[: settings.report_top_findings_limit]
    provider = get_report_provider()

    if provider is None:
        logger.info("No AI report provider configured; using fallback report")
        return _fallback_report(metrics, scores, findings, trimmed_top)

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
        return provider.generate(SYSTEM_PROMPT, user_prompt)
    except ReportProviderError as exc:
        logger.warning("%s report generation failed: %s", provider.name.title(), exc)
        return _unavailable_report(metrics, scores, findings, trimmed_top)
    except Exception:
        logger.exception("%s report generation failed unexpectedly", provider.name.title())
        return _unavailable_report(metrics, scores, findings, trimmed_top)


def _unavailable_report(
    metrics: dict,
    scores: dict,
    findings: list[dict],
    top: list[dict],
) -> str:
    return (
        AI_UNAVAILABLE_HEADER
        + "\n---\n\n"
        + _fallback_report(metrics, scores, findings, top)
    )


def _category_findings(findings: list[dict], category: str, limit: int = 8) -> list[dict]:
    return [f for f in findings if f.get("category") == category][:limit]


def _fallback_report(
    metrics: dict,
    scores: dict,
    findings: list[dict],
    top: list[dict],
) -> str:
    high_count = sum(1 for f in findings if f.get("severity") == "high")
    medium_count = sum(1 for f in findings if f.get("severity") == "medium")
    low_count = sum(1 for f in findings if f.get("severity") == "low")
    by_category = metrics.get("findings_by_category", build_findings_by_category(findings))
    dead_code = metrics.get("dead_code_summary", {})

    lines = [
        "# Repository Audit Report",
        "",
        "## Executive Summary",
        "",
        f"This repository contains **{metrics.get('files_scanned', 0)}** source files "
        f"with **{metrics.get('total_lines', 0)}** total lines of code. "
        f"The analysis identified **{len(findings)}** issues "
        f"({high_count} high, {medium_count} medium, {low_count} low severity).",
        "",
        "### Score Breakdown",
        "",
        f"- **Maintainability:** {scores.get('maintainability', 0)}/100",
        f"- **Security:** {scores.get('security', 0)}/100",
        f"- **Architecture:** {scores.get('architecture', 0)}/100",
        f"- **Dead Code:** {scores.get('dead_code', 0)}/100",
        "",
        "### Findings by Category",
        "",
    ]

    for category, count in sorted(by_category.items()):
        lines.append(f"- **{category.replace('_', ' ').title()}:** {count}")

    lines.extend(["", "## Security Assessment", ""])
    security = _category_findings(findings, "security")
    if security:
        for item in security:
            lines.append(f"- **{item.get('file')}:** {item.get('message')}")
    else:
        lines.append("No security issues detected.")

    lines.extend(["", "## Maintainability Assessment", ""])
    maintainability = [
        f for f in findings if f.get("category") == "maintainability" and f.get("type") != "duplicate_logic"
    ]
    if maintainability:
        for item in maintainability[:8]:
            lines.append(f"- {item.get('message')}")
    else:
        lines.append("No maintainability issues detected.")

    lines.extend(["", "## Dead Code Assessment", ""])
    lines.append(
        f"Unused imports: **{dead_code.get('unused_imports', 0)}**, "
        f"unused variables: **{dead_code.get('unused_variables', 0)}**, "
        f"unused functions: **{dead_code.get('unused_functions', 0)}**."
    )
    dead = _category_findings(findings, "dead_code")
    for item in dead[:8]:
        lines.append(f"- {item.get('message')}")

    lines.extend(["", "## Duplicate Logic Assessment", ""])
    duplicate_items = [f for f in findings if f.get("type") == "duplicate_logic"]
    dup_summary = metrics.get("duplicate_logic_summary", {})
    lines.append(
        f"Duplicate pairs: **{dup_summary.get('duplicate_pairs', 0)}** "
        f"(high: {dup_summary.get('high_confidence_duplicates', 0)}, "
        f"medium: {dup_summary.get('medium_confidence_duplicates', 0)}, "
        f"possible: {dup_summary.get('possible_duplicates', 0)})."
    )
    if duplicate_items:
        for item in duplicate_items[:8]:
            lines.append(f"- {item.get('message')}")
    else:
        lines.append("No semantic duplicate logic detected.")

    lines.extend(["", "## Architecture Assessment", ""])
    architecture = _category_findings(findings, "architecture")
    if architecture:
        for item in architecture:
            lines.append(f"- {item.get('message')}")
    else:
        lines.append("No architecture issues detected.")

    lines.extend(["", "## Prioritized Refactoring Plan", ""])
    prioritized = top or findings[:10]
    if prioritized:
        for index, item in enumerate(prioritized, start=1):
            lines.append(f"{index}. [{item.get('severity', 'unknown')}] {item.get('message')}")
    else:
        lines.append("No immediate actions required.")

    lines.append("")
    lines.append("*Automated summary generated without AI.*")
    return "\n".join(lines)
