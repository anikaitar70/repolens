from app.analysis_context import AnalysisContext
from app.config import settings
from app.findings import create_finding
from app.scanner import count_lines


def detect_large_files(ctx: AnalysisContext) -> list[dict]:
    findings: list[dict] = []
    threshold = settings.large_file_threshold

    for file_path in ctx.files:
        lines = count_lines(file_path)
        if lines > threshold:
            rel = ctx.rel_path(file_path)
            findings.append(
                create_finding(
                    type="large_file",
                    severity="medium",
                    category="maintainability",
                    file=rel,
                    line=1,
                    message=f"File exceeds {threshold} lines ({lines} lines)",
                    evidence={"lines": lines, "threshold": threshold},
                )
            )

    return findings
