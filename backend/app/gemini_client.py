import json

import google.generativeai as genai

from app.config import settings
from app.logging_config import get_logger
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
  5. Architecture Assessment
  6. Prioritized Refactoring Plan
- Reference specific finding IDs or messages when discussing issues.
- Be concise but actionable.
"""


def generate_report(
    metrics: dict,
    scores: dict,
    findings: list[dict],
    top: list[dict] | None = None,
) -> str:
    if not settings.gemini_api_key:
        logger.info("Gemini API key not configured; using fallback report")
        return _fallback_report(metrics, scores, findings, top or [])

    payload = {
        "metrics": metrics,
        "scores": scores,
        "findings_by_category": metrics.get("findings_by_category", build_findings_by_category(findings)),
        "dead_code_summary": metrics.get("dead_code_summary", {}),
        "top_findings": top or [],
        "findings_count": len(findings),
    }

    try:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            system_instruction=SYSTEM_PROMPT,
        )

        prompt = (
            "Generate a professional software audit report based on the following "
            "structured analysis results:\n\n"
            f"```json\n{json.dumps(payload, indent=2)}\n```"
        )

        response = model.generate_content(prompt)
        logger.info("Gemini report generated successfully")
        return response.text or _fallback_report(metrics, scores, findings, top or [])
    except Exception:
        logger.exception("Gemini report generation failed")
        return (
            _fallback_report(metrics, scores, findings, top or [])
            + "\n\n---\n\n*Note: AI report generation failed. "
            "Showing automated summary instead.*"
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
    maintainability = _category_findings(findings, "maintainability")
    if maintainability:
        for item in maintainability:
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
    lines.append("*Report generated without AI (GEMINI_API_KEY not configured).*")
    return "\n".join(lines)
