from __future__ import annotations

from collections import Counter

DEAD_CODE_TYPES = {
    "unused_import",
    "unused_variable",
    "unused_function",
}

DUPLICATE_LOGIC_TYPE = "duplicate_logic"


def build_dead_code_summary(findings: list[dict]) -> dict[str, int]:
    counts = Counter(
        finding["type"] for finding in findings if finding.get("type") in DEAD_CODE_TYPES
    )
    return {
        "unused_imports": counts.get("unused_import", 0),
        "unused_variables": counts.get("unused_variable", 0),
        "unused_functions": counts.get("unused_function", 0),
    }


def build_duplicate_logic_summary(findings: list[dict]) -> dict[str, int]:
    duplicate_findings = [f for f in findings if f.get("type") == DUPLICATE_LOGIC_TYPE]

    high = sum(1 for f in duplicate_findings if f.get("confidence") == "high")
    medium = sum(1 for f in duplicate_findings if f.get("confidence") == "medium")
    possible = sum(1 for f in duplicate_findings if f.get("confidence") == "low")

    return {
        "duplicate_pairs": len(duplicate_findings),
        "high_confidence_duplicates": high,
        "medium_confidence_duplicates": medium,
        "possible_duplicates": possible,
    }


def build_findings_by_category(findings: list[dict]) -> dict[str, int]:
    return dict(Counter(finding.get("category", "unknown") for finding in findings))


def top_findings(findings: list[dict], limit: int | None = None) -> list[dict]:
    from app.config import settings

    effective_limit = limit if limit is not None else settings.report_top_findings_limit
    severity_rank = {"high": 0, "medium": 1, "low": 2}

    def sort_key(item: dict) -> tuple:
        duplicate_boost = 0 if item.get("type") == DUPLICATE_LOGIC_TYPE else 1
        return (
            duplicate_boost,
            severity_rank.get(item.get("severity", "low"), 3),
            -float(item.get("similarity", 0) or 0),
        )

    return sorted(findings, key=sort_key)[:effective_limit]
