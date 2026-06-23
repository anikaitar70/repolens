"""Shared module dependency graph for architecture analysis."""

from __future__ import annotations

import ast
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

JS_IMPORT_PATTERN = re.compile(
    r"""import\s+(?:[\w\s{},*]+\s+from\s+)?['"]([^'"]+)['"]"""
)
JS_REQUIRE_PATTERN = re.compile(
    r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)"""
)


@dataclass
class DependencyGraph:
    """Directed graph of module-to-module imports."""

    edges: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    language: str = "mixed"

    def fan_out(self, module: str) -> int:
        return len(set(self.edges.get(module, [])))

    def fan_in(self, module: str) -> int:
        return sum(1 for source, targets in self.edges.items() if module in targets)

    def modules(self) -> set[str]:
        nodes: set[str] = set(self.edges.keys())
        for targets in self.edges.values():
            nodes.update(targets)
        return nodes

    def merge(self, other: DependencyGraph) -> DependencyGraph:
        merged = DependencyGraph(language="mixed")
        for source, targets in self.edges.items():
            merged.edges[source].extend(targets)
        for source, targets in other.edges.items():
            merged.edges[source].extend(targets)
        for source in merged.edges:
            merged.edges[source] = sorted(set(merged.edges[source]))
        return merged


def module_name_from_path(root: Path, path: Path) -> str:
    rel = path.relative_to(root)
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = Path(parts[-1]).stem
    return "/".join(parts).replace("\\", "/")


def module_to_display_path(module: str, is_python: bool) -> str:
    if is_python:
        if module.endswith("/__init__") or module == "__init__":
            return module.replace("/__init__", "/__init__.py")
        return f"{module}.py" if not module.endswith(".py") else module

    for ext in (".tsx", ".ts", ".jsx", ".js"):
        if module.endswith(ext):
            return module
    return f"{module}.ts"


def build_dependency_graphs(root: Path, files: list[Path]) -> list[DependencyGraph]:
    return [
        _build_python_graph(root, files),
        _build_js_graph(root, files),
    ]


def build_combined_graph(root: Path, files: list[Path]) -> DependencyGraph:
    graphs = build_dependency_graphs(root, files)
    combined = DependencyGraph()
    for graph in graphs:
        combined = combined.merge(graph)
    return combined


def find_cycles(graph: DependencyGraph) -> list[list[str]]:
    cycles: list[list[str]] = []
    visited: set[str] = set()
    stack: set[str] = set()
    path: list[str] = []

    def dfs(node: str) -> None:
        visited.add(node)
        stack.add(node)
        path.append(node)

        for neighbor in graph.edges.get(node, []):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in stack:
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                if cycle not in cycles:
                    cycles.append(cycle)

        path.pop()
        stack.remove(node)

    for node in graph.modules():
        if node not in visited:
            dfs(node)

    return cycles


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
        return module_name_from_path(root, target.with_suffix(".py"))
    if (target / "__init__.py").exists():
        return module_name_from_path(root, target / "__init__.py")
    return None


def _build_python_graph(root: Path, files: list[Path]) -> DependencyGraph:
    graph = DependencyGraph(language="python")
    py_files = [f for f in files if f.suffix.lower() == ".py"]

    for file_path in py_files:
        module = module_name_from_path(root, file_path)
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
                        graph.edges[module].append(resolved)
            elif isinstance(node, ast.ImportFrom):
                if node.module is None and not node.names:
                    continue
                mod = node.module or ""
                resolved = _resolve_python_import(root, file_path, mod, node.level or 0)
                if resolved and resolved != module:
                    graph.edges[module].append(resolved)

    for source in graph.edges:
        graph.edges[source] = sorted(set(graph.edges[source]))
    return graph


def _resolve_js_import(root: Path, source_file: Path, import_path: str) -> str | None:
    if not import_path.startswith("."):
        return None

    try:
        base = (source_file.parent / import_path).resolve()
        base.relative_to(root.resolve())
    except ValueError:
        return None

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
                return module_name_from_path(root, candidate)
            except ValueError:
                return None
    return None


def _build_js_graph(root: Path, files: list[Path]) -> DependencyGraph:
    graph = DependencyGraph(language="javascript")
    js_files = [f for f in files if f.suffix.lower() in {".js", ".jsx", ".ts", ".tsx"}]

    for file_path in js_files:
        module = module_name_from_path(root, file_path)
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
                graph.edges[module].append(resolved)

    for source in graph.edges:
        graph.edges[source] = sorted(set(graph.edges[source]))
    return graph
