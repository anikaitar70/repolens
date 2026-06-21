from __future__ import annotations

from collections import Counter

DEAD_CODE_TYPES = {
    "unused_import",
    "unused_variable",
    "unused_function",
}


def build_dead_code_summary(findings: list[dict]) -> dict[str, int]:
    counts = Counter(
        finding["type"] for finding in findings if finding.get("type") in DEAD_CODE_TYPES
    )
    return {
        "unused_imports": counts.get("unused_import", 0),
        "unused_variables": counts.get("unused_variable", 0),
        "unused_functions": counts.get("unused_function", 0),
    }


def build_findings_by_category(findings: list[dict]) -> dict[str, int]:
    return dict(Counter(finding.get("category", "unknown") for finding in findings))


def top_findings(findings: list[dict], limit: int | None = None) -> list[dict]:
    from app.config import settings

    effective_limit = limit if limit is not None else settings.gemini_top_findings_limit
    severity_rank = {"high": 0, "medium": 1, "low": 2}

    def sort_key(item: dict) -> tuple[int, str]:
        return (severity_rank.get(item.get("severity", "low"), 3), item.get("type", ""))

    return sorted(findings, key=sort_key)[:effective_limit]
