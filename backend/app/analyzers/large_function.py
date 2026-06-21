import ast
import re

from app.analysis_context import AnalysisContext
from app.config import settings
from app.findings import create_finding

JS_FUNCTION_PATTERN = re.compile(
    r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*\{",
    re.MULTILINE,
)
JS_ARROW_PATTERN = re.compile(
    r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>\s*\{",
    re.MULTILINE,
)
JS_METHOD_PATTERN = re.compile(
    r"(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{",
    re.MULTILINE,
)


def _python_functions(content: str, file_path: str, threshold: int) -> list[dict]:
    findings: list[dict] = []

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return findings

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.end_lineno or not node.lineno:
                continue
            lines = node.end_lineno - node.lineno + 1
            if lines > threshold:
                findings.append(
                    create_finding(
                        type="large_function",
                        severity="medium",
                        category="maintainability",
                        file=file_path,
                        line=node.lineno,
                        message=f"Function '{node.name}' is {lines} lines (threshold: {threshold})",
                        evidence={"function": node.name, "lines": lines, "threshold": threshold},
                    )
                )

    return findings


def _find_matching_brace(content: str, open_index: int) -> int | None:
    depth = 0
    for i in range(open_index, len(content)):
        if content[i] == "{":
            depth += 1
        elif content[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return None


def _js_functions(content: str, file_path: str, threshold: int) -> list[dict]:
    findings: list[dict] = []
    seen: set[tuple[str, int]] = set()
    patterns = [JS_FUNCTION_PATTERN, JS_ARROW_PATTERN, JS_METHOD_PATTERN]

    for pattern in patterns:
        for match in pattern.finditer(content):
            name = match.group(1)
            brace_start = content.find("{", match.end() - 1)
            if brace_start == -1:
                continue

            brace_end = _find_matching_brace(content, brace_start)
            if brace_end is None:
                continue

            start_line = content[: match.start()].count("\n") + 1
            end_line = content[: brace_end].count("\n") + 1
            key = (name, start_line)

            if key in seen:
                continue
            seen.add(key)

            lines = end_line - start_line + 1
            if lines > threshold:
                findings.append(
                    create_finding(
                        type="large_function",
                        severity="medium",
                        category="maintainability",
                        file=file_path,
                        line=start_line,
                        message=f"Function '{name}' is {lines} lines (threshold: {threshold})",
                        evidence={"function": name, "lines": lines, "threshold": threshold},
                    )
                )

    return findings


def detect_large_functions(ctx: AnalysisContext) -> list[dict]:
    findings: list[dict] = []
    threshold = settings.large_function_threshold

    for file_path in ctx.files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        rel = ctx.rel_path(file_path)
        ext = file_path.suffix.lower()

        if ext == ".py":
            findings.extend(_python_functions(content, rel, threshold))
        elif ext in {".js", ".jsx", ".ts", ".tsx"}:
            findings.extend(_js_functions(content, rel, threshold))

    return findings
