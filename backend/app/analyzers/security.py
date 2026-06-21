import re

from app.analysis_context import AnalysisContext
from app.findings import create_finding

SECURITY_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("Dangerous eval() usage", re.compile(r"\beval\s*\("), "high"),
    ("Dangerous exec() usage", re.compile(r"\bexec\s*\("), "high"),
    ("Unsafe innerHTML assignment", re.compile(r"\.innerHTML\s*="), "high"),
    (
        "Hardcoded Password",
        re.compile(r"""(?i)(?:password|passwd|pwd)\s*[=:]\s*['"][^'"]{3,}['"]"""),
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


def detect_security_issues(ctx: AnalysisContext) -> list[dict]:
    findings: list[dict] = []

    for file_path in ctx.files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        rel = ctx.rel_path(file_path)
        lines = content.splitlines()

        for issue_name, pattern, severity in SECURITY_PATTERNS:
            for line_num, line in enumerate(lines, start=1):
                if pattern.search(line):
                    stripped = line.strip()
                    if stripped.startswith("#") or stripped.startswith("//"):
                        continue

                    findings.append(
                        create_finding(
                            type="security",
                            severity=severity,
                            category="security",
                            file=rel,
                            line=line_num,
                            message=f"{issue_name} detected at line {line_num}",
                            evidence={"issue": issue_name},
                        )
                    )

    return findings
