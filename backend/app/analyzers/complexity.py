from radon.complexity import cc_visit

from app.analysis_context import AnalysisContext
from app.config import settings
from app.findings import create_finding


def analyze_complexity(ctx: AnalysisContext) -> list[dict]:
    """Analyze cyclomatic complexity for Python files using Radon."""
    findings: list[dict] = []
    threshold = settings.complexity_threshold

    for file_path in ctx.files:
        if file_path.suffix.lower() != ".py":
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        try:
            blocks = cc_visit(content)
        except Exception:
            continue

        rel = ctx.rel_path(file_path)

        for block in blocks:
            if block.complexity >= threshold:
                findings.append(
                    create_finding(
                        type="complexity",
                        severity="high",
                        category="maintainability",
                        file=rel,
                        line=block.lineno,
                        message=(
                            f"Function '{block.name}' has cyclomatic complexity "
                            f"{block.complexity} (threshold: {threshold})"
                        ),
                        evidence={
                            "function": block.name,
                            "complexity": block.complexity,
                            "threshold": threshold,
                        },
                    )
                )

    return findings
