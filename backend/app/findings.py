import uuid
from typing import Any


def create_finding(
    *,
    type: str,
    severity: str,
    category: str,
    file: str,
    message: str,
    line: int = 0,
    confidence: str = "",
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "type": type,
        "severity": severity,
        "category": category,
        "file": file,
        "line": line,
        "message": message,
        "confidence": confidence,
        "evidence": evidence or {},
    }
