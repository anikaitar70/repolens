import json

import google.generativeai as genai

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a senior software architect writing a professional repository audit report.

You will receive structured analysis data containing metrics, scores, and findings from automated static analysis tools.

Rules:
- Base your report ONLY on the provided data.
- Do NOT invent issues not present in the findings.
- Do NOT request or assume access to source code.
- Write in clear, professional markdown.
- Include these sections exactly:
  1. Executive Summary
  2. Critical Issues
  3. Security Concerns
  4. Technical Debt Assessment
  5. Refactoring Recommendations
  6. Priority Action Plan
- Reference specific findings when discussing issues.
- Be concise but actionable.
"""


def generate_report(metrics: dict, scores: dict, findings: list[dict]) -> str:
    if not settings.gemini_api_key:
        logger.info("Gemini API key not configured; using fallback report")
        return _fallback_report(metrics, scores, findings)

    payload = {
        "metrics": metrics,
        "scores": scores,
        "findings": findings,
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
        return response.text or _fallback_report(metrics, scores, findings)
    except Exception:
        logger.exception("Gemini report generation failed")
        return (
            _fallback_report(metrics, scores, findings)
            + "\n\n---\n\n*Note: AI report generation failed. "
            "Showing automated summary instead.*"
        )


def _fallback_report(metrics: dict, scores: dict, findings: list[dict]) -> str:
    high_count = sum(1 for f in findings if f.get("severity") == "high")
    medium_count = sum(1 for f in findings if f.get("severity") == "medium")

    lines = [
        "# Repository Audit Report",
        "",
        "## Executive Summary",
        "",
        f"This repository contains **{metrics.get('files_scanned', 0)}** source files "
        f"with **{metrics.get('total_lines', 0)}** total lines of code. "
        f"The analysis identified **{len(findings)}** issues "
        f"({high_count} high severity, {medium_count} medium severity).",
        "",
        "## Scores",
        "",
        f"- **Maintainability:** {scores.get('maintainability', 0)}/100",
        f"- **Security:** {scores.get('security', 0)}/100",
        f"- **Architecture:** {scores.get('architecture', 0)}/100",
        "",
        "## Critical Issues",
        "",
    ]

    critical = [f for f in findings if f.get("severity") == "high"]
    if critical:
        for item in critical[:10]:
            lines.append(f"- {item.get('description', item.get('issue', 'Unknown issue'))}")
    else:
        lines.append("No critical issues detected.")

    lines.extend(["", "## Security Concerns", ""])
    security = [f for f in findings if f.get("type") == "security"]
    if security:
        for item in security:
            lines.append(
                f"- **{item.get('file', 'unknown')}:** {item.get('issue', 'Security issue')}"
            )
    else:
        lines.append("No security issues detected.")

    lines.extend(["", "## Technical Debt Assessment", ""])
    debt_types = {"large_file", "large_function", "complexity"}
    debt = [f for f in findings if f.get("type") in debt_types]
    lines.append(f"Found {len(debt)} maintainability-related findings affecting code quality.")

    lines.extend(["", "## Refactoring Recommendations", ""])
    if debt:
        lines.append("- Break down large functions into smaller, focused units.")
        lines.append("- Split oversized files into modules with clear responsibilities.")
        lines.append("- Reduce cyclomatic complexity in flagged functions.")
    else:
        lines.append("- Continue maintaining current code organization practices.")

    lines.extend(["", "## Priority Action Plan", ""])
    if findings:
        lines.append("1. Address all high-severity security findings immediately.")
        lines.append("2. Resolve circular dependency chains to improve architecture.")
        lines.append("3. Refactor the highest-complexity functions.")
        lines.append("4. Split the largest files to improve maintainability.")
    else:
        lines.append("No immediate actions required. Continue monitoring code quality.")

    lines.append("")
    lines.append("*Report generated without AI (GEMINI_API_KEY not configured).*")

    return "\n".join(lines)
