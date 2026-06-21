import ast
import re
from collections import defaultdict
from pathlib import Path

from app.analysis_context import AnalysisContext
from app.findings import create_finding

JS_IMPORT_PATTERN = re.compile(
    r"""import\s+(?:[\w\s{},*]+\s+from\s+)?['"]([^'"]+)['"]"""
)
JS_REQUIRE_PATTERN = re.compile(
    r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)"""
)


def _module_name_from_path(root: Path, path: Path) -> str:
    rel = path.relative_to(root)
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = Path(parts[-1]).stem
    return "/".join(parts).replace("\\", "/")


def _resolve_python_import(
    root: Path, source_file: Path, module: str, level: int
) -> str | None:
    base_parts = list(source_file.relative_to(root).parent.parts)

    if level > 0:
        if level > len(base_parts) + 1:
            return None
        package_parts = base_parts[: len(base_parts) - level + 1]
    else:
        package_parts = []

    module_parts = module.split(".") if module else []
    target = root.joinpath(*package_parts, *module_parts)

    if target.with_suffix(".py").exists():
        return _module_name_from_path(root, target.with_suffix(".py"))
    if (target / "__init__.py").exists():
        return _module_name_from_path(root, target / "__init__.py")
    return None


def _build_python_graph(root: Path, files: list[Path]) -> dict[str, list[str]]:
    graph: dict[str, list[str]] = defaultdict(list)
    py_files = [f for f in files if f.suffix.lower() == ".py"]

    for file_path in py_files:
        module = _module_name_from_path(root, file_path)
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content)
        except (OSError, SyntaxError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    resolved = _resolve_python_import(root, file_path, alias.name, 0)
                    if resolved and resolved != module:
                        graph[module].append(resolved)
            elif isinstance(node, ast.ImportFrom):
                if node.module is None and not node.names:
                    continue
                mod = node.module or ""
                resolved = _resolve_python_import(root, file_path, mod, node.level or 0)
                if resolved and resolved != module:
                    graph[module].append(resolved)

    return graph


def _resolve_js_import(root: Path, source_file: Path, import_path: str) -> str | None:
    if not import_path.startswith("."):
        return None

    base = (source_file.parent / import_path).resolve()
    candidates = [
        base,
        base.with_suffix(".js"),
        base.with_suffix(".jsx"),
        base.with_suffix(".ts"),
        base.with_suffix(".tsx"),
        base / "index.js",
        base / "index.ts",
        base / "index.tsx",
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            try:
                return _module_name_from_path(root, candidate)
            except ValueError:
                return None
    return None


def _build_js_graph(root: Path, files: list[Path]) -> dict[str, list[str]]:
    graph: dict[str, list[str]] = defaultdict(list)
    js_files = [f for f in files if f.suffix.lower() in {".js", ".jsx", ".ts", ".tsx"}]

    for file_path in js_files:
        module = _module_name_from_path(root, file_path)
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        imports: set[str] = set()
        for pattern in (JS_IMPORT_PATTERN, JS_REQUIRE_PATTERN):
            for match in pattern.finditer(content):
                imports.add(match.group(1))

        for import_path in imports:
            resolved = _resolve_js_import(root, file_path, import_path)
            if resolved and resolved != module:
                graph[module].append(resolved)

    return graph


def _find_cycles(graph: dict[str, list[str]]) -> list[list[str]]:
    cycles: list[list[str]] = []
    visited: set[str] = set()
    stack: set[str] = set()
    path: list[str] = []

    def dfs(node: str) -> None:
        visited.add(node)
        stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in stack:
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                if cycle not in cycles:
                    cycles.append(cycle)

        path.pop()
        stack.remove(node)

    for node in graph:
        if node not in visited:
            dfs(node)

    return cycles


def _module_to_display_path(module: str, is_python: bool) -> str:
    if is_python:
        if module.endswith("/__init__") or module == "__init__":
            return module.replace("/__init__", "/__init__.py") + (
                "" if module.endswith(".py") else ""
            )
        return f"{module}.py" if not module.endswith(".py") else module

    for ext in (".tsx", ".ts", ".jsx", ".js"):
        if module.endswith(ext):
            return module
    return f"{module}.ts"


def detect_circular_imports(ctx: AnalysisContext) -> list[dict]:
    findings: list[dict] = []
    root = ctx.root
    files = ctx.files

    for graph, is_python in ((_build_python_graph(root, files), True), (_build_js_graph(root, files), False)):
        for cycle in _find_cycles(graph):
            chain = [_module_to_display_path(m, is_python) for m in cycle]
            chain_str = " -> ".join(cycle[:-1] + [cycle[0]])
            findings.append(
                create_finding(
                    type="circular_dependency",
                    severity="high",
                    category="architecture",
                    file=chain[0] if chain else "",
                    line=0,
                    message=f"Circular dependency detected: {chain_str}",
                    evidence={"issue": "Circular Dependency", "chain": chain},
                )
            )

    return findings
