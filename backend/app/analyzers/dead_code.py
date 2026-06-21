from __future__ import annotations

from dataclasses import dataclass

from tree_sitter import Node

from app.analysis_context import AnalysisContext
from app.findings import create_finding
from app.services.ast_parser import ASTParser, ParsedFile

ENTRYPOINT_FUNCTION_NAMES = {
    "main",
    "run",
    "setup",
    "create_app",
    "handler",
    "app",
    "index",
    "__init__",
}

PYTHON_IMPORT_NODES = {"import_statement", "import_from_statement"}
JS_IMPORT_NODES = {"import_statement"}
PYTHON_FUNCTION_NODES = {"function_definition"}
JS_FUNCTION_NODES = {"function_declaration", "method_definition", "arrow_function"}


@dataclass
class ImportBinding:
    name: str
    line: int
    node: Node


def analyze_dead_code(ctx: AnalysisContext) -> list[dict]:
    parsed_files = ctx.get_parsed_files()
    project_references = _collect_project_references(parsed_files)

    findings: list[dict] = []
    for parsed in parsed_files:
        findings.extend(_detect_unused_imports(parsed))
        findings.extend(_detect_unused_variables(parsed))
        findings.extend(_detect_unused_functions(parsed, project_references))
    return findings


def _collect_project_references(parsed_files: list[ParsedFile]) -> set[str]:
    references: set[str] = set()
    for parsed in parsed_files:
        references.update(_collect_identifiers(parsed, exclude_imports=True))
        references.update(_collect_call_names(parsed))
    return references


def _collect_identifiers(parsed: ParsedFile, exclude_imports: bool = False) -> set[str]:
    names: set[str] = set()
    for node in ASTParser.walk(parsed.tree.root_node):
        if node.type != "identifier":
            continue
        if exclude_imports and _is_in_import(parsed, node):
            continue
        if _is_definition_name(parsed, node):
            continue
        names.add(ASTParser.node_text(parsed, node))
    return names


def _collect_call_names(parsed: ParsedFile) -> set[str]:
    names: set[str] = set()
    for node in ASTParser.walk(parsed.tree.root_node):
        if node.type not in {"call", "call_expression"}:
            continue
        function_node = node.child_by_field_name("function")
        if function_node is None:
            continue
        if function_node.type == "identifier":
            names.add(ASTParser.node_text(parsed, function_node))
        elif function_node.type == "attribute":
            attr = function_node.child_by_field_name("attribute")
            if attr is not None:
                names.add(ASTParser.node_text(parsed, attr))
    return names


def _detect_unused_imports(parsed: ParsedFile) -> list[dict]:
    bindings = _extract_import_bindings(parsed)
    if not bindings:
        return []

    used = _collect_identifiers(parsed, exclude_imports=True)
    findings: list[dict] = []

    for binding in bindings:
        if binding.name == "*":
            continue
        if binding.name not in used:
            findings.append(
                create_finding(
                    type="unused_import",
                    severity="low",
                    category="dead_code",
                    file=parsed.rel_path,
                    line=binding.line,
                    message=f"Import '{binding.name}' is never used",
                    confidence="high",
                    evidence={"symbol": binding.name},
                )
            )
    return findings


def _detect_unused_variables(parsed: ParsedFile) -> list[dict]:
    declarations = _extract_variable_declarations(parsed)
    if not declarations:
        return []

    used = _collect_identifiers(parsed, exclude_imports=True)
    findings: list[dict] = []

    for name, line in declarations:
        if name not in used:
            findings.append(
                create_finding(
                    type="unused_variable",
                    severity="low",
                    category="dead_code",
                    file=parsed.rel_path,
                    line=line,
                    message=f"Variable '{name}' is declared but never used",
                    confidence="high",
                    evidence={"variable": name},
                )
            )
    return findings


def _detect_unused_functions(parsed: ParsedFile, project_references: set[str]) -> list[dict]:
    functions = _extract_function_definitions(parsed)
    if len(functions) > 30:
        return []

    findings: list[dict] = []

    for name, line, exported, is_dunder in functions:
        if exported or is_dunder or name in ENTRYPOINT_FUNCTION_NAMES:
            continue
        if name.startswith("test_") and parsed.rel_path.endswith((".py", ".ts", ".js")):
            if "test" in parsed.path.name.lower():
                continue
        if name in project_references:
            continue

        confidence = _function_confidence(name, exported)
        findings.append(
            create_finding(
                type="unused_function",
                severity="medium",
                category="dead_code",
                file=parsed.rel_path,
                line=line,
                message=f"Function '{name}' appears to be unused",
                confidence=confidence,
                evidence={"function": name},
            )
        )
    return findings


def _function_confidence(name: str, exported: bool) -> str:
    if exported:
        return "low"
    if name.startswith("_"):
        return "high"
    return "medium"


def _extract_import_bindings(parsed: ParsedFile) -> list[ImportBinding]:
    bindings: list[ImportBinding] = []

    if parsed.language == "python":
        for node in ASTParser.walk(parsed.tree.root_node):
            if node.type == "import_statement":
                for child in node.children:
                    if child.type == "dotted_name":
                        bindings.append(
                            ImportBinding(
                                name=ASTParser.node_text(parsed, child).split(".")[0],
                                line=ASTParser.line_number(parsed, child),
                                node=child,
                            )
                        )
                    elif child.type == "aliased_import":
                        alias = child.child_by_field_name("alias")
                        name_node = child.child_by_field_name("name")
                        bindings.append(
                            ImportBinding(
                                name=ASTParser.node_text(parsed, alias or name_node),
                                line=ASTParser.line_number(parsed, child),
                                node=child,
                            )
                        )
            elif node.type == "import_from_statement":
                for child in node.children:
                    if child.type == "dotted_name" and child == node.child_by_field_name("module_name"):
                        continue
                    if child.type == "wildcard_import":
                        bindings.append(
                            ImportBinding(name="*", line=ASTParser.line_number(parsed, child), node=child)
                        )
                    elif child.type == "aliased_import":
                        alias = child.child_by_field_name("alias")
                        name_node = child.child_by_field_name("name")
                        bindings.append(
                            ImportBinding(
                                name=ASTParser.node_text(parsed, alias or name_node),
                                line=ASTParser.line_number(parsed, child),
                                node=child,
                            )
                        )
                    elif child.type == "identifier":
                        bindings.append(
                            ImportBinding(
                                name=ASTParser.node_text(parsed, child),
                                line=ASTParser.line_number(parsed, child),
                                node=child,
                            )
                        )
    else:
        for node in ASTParser.walk(parsed.tree.root_node):
            if node.type != "import_statement":
                continue
            default_binding = node.child_by_field_name("name")
            if default_binding is not None:
                bindings.append(
                    ImportBinding(
                        name=ASTParser.node_text(parsed, default_binding),
                        line=ASTParser.line_number(parsed, default_binding),
                        node=default_binding,
                    )
                )
            for child in node.children:
                if child.type == "import_clause":
                    for clause_child in child.children:
                        if clause_child.type == "identifier":
                            bindings.append(
                                ImportBinding(
                                    name=ASTParser.node_text(parsed, clause_child),
                                    line=ASTParser.line_number(parsed, clause_child),
                                    node=clause_child,
                                )
                            )
                        elif clause_child.type == "named_imports":
                            for spec in clause_child.children:
                                if spec.type == "import_specifier":
                                    alias = spec.child_by_field_name("alias")
                                    name_node = spec.child_by_field_name("name")
                                    bindings.append(
                                        ImportBinding(
                                            name=ASTParser.node_text(parsed, alias or name_node),
                                            line=ASTParser.line_number(parsed, spec),
                                            node=spec,
                                        )
                                    )
                elif child.type == "namespace_import":
                    alias = child.child_by_field_name("alias")
                    if alias is not None:
                        bindings.append(
                            ImportBinding(
                                name=ASTParser.node_text(parsed, alias),
                                line=ASTParser.line_number(parsed, alias),
                                node=alias,
                            )
                        )
    return bindings


def _extract_variable_declarations(parsed: ParsedFile) -> list[tuple[str, int]]:
    declarations: list[tuple[str, int]] = []

    if parsed.language == "python":
        for node in ASTParser.walk(parsed.tree.root_node):
            if node.type == "assignment":
                left = node.child_by_field_name("left")
                if left is None:
                    continue
                if left.type == "identifier":
                    name = ASTParser.node_text(parsed, left)
                    if not name.startswith("_"):
                        declarations.append((name, ASTParser.line_number(parsed, left)))
                elif left.type == "tuple_pattern":
                    for child in left.children:
                        if child.type == "identifier":
                            name = ASTParser.node_text(parsed, child)
                            declarations.append((name, ASTParser.line_number(parsed, child)))
            elif node.type == "expression_statement":
                child = node.children[0] if node.children else None
                if child is not None and child.type == "assignment":
                    left = child.child_by_field_name("left")
                    if left is not None and left.type == "identifier":
                        name = ASTParser.node_text(parsed, left)
                        declarations.append((name, ASTParser.line_number(parsed, left)))
    else:
        for node in ASTParser.walk(parsed.tree.root_node):
            if node.type not in {"lexical_declaration", "variable_declaration"}:
                continue
            for child in node.children:
                if child.type != "variable_declarator":
                    continue
                name_node = child.child_by_field_name("name")
                if name_node is not None and name_node.type == "identifier":
                    name = ASTParser.node_text(parsed, name_node)
                    declarations.append((name, ASTParser.line_number(parsed, name_node)))

    return declarations


def _extract_function_definitions(parsed: ParsedFile) -> list[tuple[str, int, bool, bool]]:
    functions: list[tuple[str, int, bool, bool]] = []

    if parsed.language == "python":
        for node in ASTParser.walk(parsed.tree.root_node):
            if node.type != "function_definition":
                continue
            if node.parent and node.parent.type not in {"module", "block"}:
                if node.parent.type == "class_definition":
                    continue
            name_node = node.child_by_field_name("name")
            if name_node is None:
                continue
            name = ASTParser.node_text(parsed, name_node)
            functions.append(
                (
                    name,
                    ASTParser.line_number(parsed, name_node),
                    False,
                    name.startswith("__") and name.endswith("__"),
                )
            )
    else:
        for node in ASTParser.walk(parsed.tree.root_node):
            if node.type not in {"function_declaration", "method_definition"}:
                continue
            if node.parent and node.parent.type == "class_declaration":
                continue
            name_node = node.child_by_field_name("name")
            if name_node is None:
                continue
            name = ASTParser.node_text(parsed, name_node)
            exported = _is_exported(parsed, node)
            functions.append(
                (
                    name,
                    ASTParser.line_number(parsed, name_node),
                    exported,
                    False,
                )
            )

    return functions


def _is_exported(parsed: ParsedFile, node: Node) -> bool:
    current = node.parent
    while current is not None:
        if current.type in {"export_statement", "export_clause"}:
            return True
        if current.type == "program":
            break
        current = current.parent
    return False


def _is_in_import(parsed: ParsedFile, node: Node) -> bool:
    current = node.parent
    while current is not None:
        if current.type in PYTHON_IMPORT_NODES | JS_IMPORT_NODES:
            return True
        if current.type in {"program", "module"}:
            break
        current = current.parent
    return False


def _is_definition_name(parsed: ParsedFile, node: Node) -> bool:
    parent = node.parent
    if parent is None:
        return False

    if parsed.language == "python":
        if parent.type == "function_definition" and parent.child_by_field_name("name") == node:
            return True
        if parent.type in {"import_statement", "import_from_statement", "aliased_import"}:
            return True
        if parent.type == "assignment" and parent.child_by_field_name("left") == node:
            return True
        if parent.type == "parameters" and node.type == "identifier":
            return True
        if parent.type in {"class_definition"} and parent.child_by_field_name("name") == node:
            return True
    else:
        if parent.type in {"function_declaration", "method_definition"} and parent.child_by_field_name("name") == node:
            return True
        if parent.type == "variable_declarator" and parent.child_by_field_name("name") == node:
            return True
        if parent.type == "import_specifier":
            return True
        if parent.type in {"formal_parameters", "required_parameter", "optional_parameter"}:
            return True
    return False
