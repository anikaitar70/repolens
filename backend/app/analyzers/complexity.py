from pathlib import Path

from radon.complexity import cc_visit

from app.config import settings
from app.scanner import relative_path


def analyze_complexity(root: Path, files: list[Path]) -> list[dict]:
    """Analyze cyclomatic complexity for Python files using Radon."""
    findings: list[dict] = []
    threshold = settings.complexity_threshold

    for file_path in files:
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

        rel = relative_path(root, file_path)

        for block in blocks:
            if block.complexity >= threshold:
                findings.append(
                    {
                        "type": "complexity",
                        "severity": "high",
                        "function": block.name,
                        "file": rel,
                        "complexity": block.complexity,
                        "description": (
                            f"Function '{block.name}' has cyclomatic complexity "
                            f"{block.complexity} (threshold: {threshold})"
                        ),
                    }
                )

    return findings
