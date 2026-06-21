def compute_scores(findings: list[dict]) -> dict[str, int]:
    maintainability = 100
    security = 100
    architecture = 100

    for finding in findings:
        ftype = finding.get("type")

        if ftype == "large_file":
            maintainability -= 5
        elif ftype == "large_function":
            maintainability -= 2
        elif ftype == "complexity":
            maintainability -= 3
        elif ftype == "security":
            security -= 10
        elif ftype == "architecture":
            architecture -= 5

    return {
        "maintainability": max(0, min(100, maintainability)),
        "security": max(0, min(100, security)),
        "architecture": max(0, min(100, architecture)),
    }
