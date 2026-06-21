import re
from pathlib import Path

from app.scanner import relative_path

SECURITY_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("Dangerous eval() usage", re.compile(r"\beval\s*\("), "high"),
    ("Dangerous exec() usage", re.compile(r"\bexec\s*\("), "high"),
    ("Unsafe innerHTML assignment", re.compile(r"\.innerHTML\s*="), "high"),
    (
        "Hardcoded Password",
        re.compile(
            r"""(?i)(?:password|passwd|pwd)\s*[=:]\s*['"][^'"]{3,}['"]"""
        ),
        "high",
    ),
    (
        "Hardcoded Secret",
        re.compile(
            r"""(?i)(?:secret|client_secret|private_key)\s*[=:]\s*['"][^'"]{3,}['"]"""
        ),
        "high",
    ),
    (
        "Hardcoded API Key",
        re.compile(
            r"""(?i)(?:api_key|apikey|api-key|access_token)\s*[=:]\s*['"][^'"]{8,}['"]"""
        ),
        "high",
    ),
]


def detect_security_issues(root: Path, files: list[Path]) -> list[dict]:
    findings: list[dict] = []

    for file_path in files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        rel = relative_path(root, file_path)
        lines = content.splitlines()

        for issue_name, pattern, severity in SECURITY_PATTERNS:
            for line_num, line in enumerate(lines, start=1):
                if pattern.search(line):
                    stripped = line.strip()
                    if stripped.startswith("#") or stripped.startswith("//"):
                        continue

                    findings.append(
                        {
                            "type": "security",
                            "severity": severity,
                            "file": rel,
                            "line": line_num,
                            "issue": issue_name,
                            "description": f"{issue_name} detected at line {line_num}",
                        }
                    )

    return findings
