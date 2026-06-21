from __future__ import annotations

import ast
import uuid
from dataclasses import dataclass

from tree_sitter import Node

from app.analysis_context import AnalysisContext
from app.services.ast_parser import ASTParser, ParsedFile

FUNCTION_NODE_TYPES = {
    "function_definition",
    "function_declaration",
    "method_definition",
    "generator_function_declaration",
}


@dataclass(frozen=True)
class ExtractedFunction:
    id: str
    name: str
    file: str
    start_line: int
    end_line: int
    source: str
    language: str

    @property
    def line_count(self) -> int:
        return self.end_line - self.start_line + 1


def extract_functions(ctx: AnalysisContext) -> list[ExtractedFunction]:
    functions: list[ExtractedFunction] = []

    for parsed in ctx.get_parsed_files():
        if parsed.language == "python":
            functions.extend(_extract_python_functions(parsed))
        else:
            functions.extend(_extract_tree_sitter_functions(parsed))

    return functions


def _extract_python_functions(parsed: ParsedFile) -> list[ExtractedFunction]:
    results: list[ExtractedFunction] = []

    try:
        tree = ast.parse(parsed.text)
    except SyntaxError:
        return results

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.end_lineno or not node.lineno:
            continue

        lines = parsed.text.splitlines()
        source = "\n".join(lines[node.lineno - 1 : node.end_lineno])
        results.append(
            ExtractedFunction(
                id=f"func_{uuid.uuid4().hex[:8]}",
                name=node.name,
                file=parsed.rel_path,
                start_line=node.lineno,
                end_line=node.end_lineno,
                source=source,
                language=parsed.language,
            )
        )

    return results


def _extract_tree_sitter_functions(parsed: ParsedFile) -> list[ExtractedFunction]:
    results: list[ExtractedFunction] = []
    seen: set[tuple[str, int]] = set()

    for node in ASTParser.walk(parsed.tree.root_node):
        if node.type in FUNCTION_NODE_TYPES:
            fn = _function_from_node(parsed, node)
            if fn and (fn.name, fn.start_line) not in seen:
                seen.add((fn.name, fn.start_line))
                results.append(fn)
        elif node.type == "lexical_declaration" or node.type == "variable_declaration":
            for child in node.children:
                if child.type != "variable_declarator":
                    continue
                name_node = child.child_by_field_name("name")
                value_node = child.child_by_field_name("value")
                if (
                    name_node is None
                    or value_node is None
                    or value_node.type != "arrow_function"
                ):
                    continue
                fn = _function_from_node(
                    parsed,
                    value_node,
                    override_name=ASTParser.node_text(parsed, name_node),
                )
                if fn and (fn.name, fn.start_line) not in seen:
                    seen.add((fn.name, fn.start_line))
                    results.append(fn)

    return results


def _function_from_node(
    parsed: ParsedFile,
    node: Node,
    override_name: str | None = None,
) -> ExtractedFunction | None:
    name_node = node.child_by_field_name("name")
    if override_name:
        name = override_name
    elif name_node is not None:
        name = ASTParser.node_text(parsed, name_node)
    else:
        return None

    start_line = node.start_point[0] + 1
    end_line = node.end_point[0] + 1
    source = ASTParser.node_text(parsed, node)

    if not source.strip():
        return None

    return ExtractedFunction(
        id=f"func_{uuid.uuid4().hex[:8]}",
        name=name,
        file=parsed.rel_path,
        start_line=start_line,
        end_line=end_line,
        source=source,
        language=parsed.language,
    )
