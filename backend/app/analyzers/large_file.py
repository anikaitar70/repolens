from pathlib import Path

from app.config import settings
from app.scanner import count_lines, relative_path


def detect_large_files(root: Path, files: list[Path]) -> list[dict]:
    findings: list[dict] = []
    threshold = settings.large_file_threshold

    for file_path in files:
        lines = count_lines(file_path)
        if lines > threshold:
            findings.append(
                {
                    "type": "large_file",
                    "severity": "medium",
                    "file": relative_path(root, file_path),
                    "lines": lines,
                    "description": f"File exceeds {threshold} lines ({lines} lines)",
                }
            )

    return findings
