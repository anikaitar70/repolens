def compute_scores(findings: list[dict]) -> dict[str, int]:
    maintainability = 100
    security = 100
    architecture = 100
    dead_code = 100

    for finding in findings:
        ftype = finding.get("type")

        if ftype == "large_file":
            maintainability -= 5
        elif ftype == "large_function":
            maintainability -= 2
        elif ftype == "complexity":
            maintainability -= 3
        elif ftype == "duplicate_logic":
            confidence = finding.get("confidence", "low")
            if confidence == "high":
                maintainability -= 4
            elif confidence == "medium":
                maintainability -= 2
            else:
                maintainability -= 1
        elif ftype == "security":
            security -= 10
        elif ftype in {"architecture", "circular_dependency"}:
            architecture -= 5
        elif ftype == "unused_import":
            dead_code -= 1
        elif ftype == "unused_variable":
            dead_code -= 2
        elif ftype == "unused_function":
            dead_code -= 3

    return {
        "maintainability": max(0, min(100, maintainability)),
        "security": max(0, min(100, security)),
        "architecture": max(0, min(100, architecture)),
        "dead_code": max(0, min(100, dead_code)),
    }
