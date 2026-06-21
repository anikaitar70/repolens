"""
Code normalization strategy for semantic duplicate detection.

Steps:
1. Remove comments (#, //, /* */)
2. Collapse whitespace and strip empty lines
3. Rename identifiers to positional placeholders (var_0, var_1, ...)
   in order of first appearance, preserving keywords and builtins
4. Lowercase remaining text for case-insensitive structural comparison

Goal: two functions with identical control flow but different variable names
should produce identical or near-identical normalized strings before embedding.
"""

from __future__ import annotations

import re

PYTHON_KEYWORDS = {
    "False", "None", "True", "and", "as", "assert", "async", "await", "break",
    "class", "continue", "def", "del", "elif", "else", "except", "finally",
    "for", "from", "global", "if", "import", "in", "is", "lambda", "nonlocal",
    "not", "or", "pass", "raise", "return", "try", "while", "with", "yield",
}

JS_KEYWORDS = {
    "async", "await", "break", "case", "catch", "class", "const", "continue",
    "debugger", "default", "delete", "do", "else", "export", "extends", "false",
    "finally", "for", "function", "if", "import", "in", "instanceof", "let",
    "new", "null", "return", "super", "switch", "this", "throw", "true", "try",
    "typeof", "undefined", "var", "void", "while", "with", "yield",
}

BUILTINS = {
    "print", "len", "range", "str", "int", "float", "bool", "list", "dict",
    "set", "tuple", "console", "Math", "Object", "Array", "JSON",
}

IDENTIFIER_PATTERN = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
BLOCK_COMMENT_PATTERN = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT_PATTERN = re.compile(r"(//.*?$|#.*?$)", re.MULTILINE)
WHITESPACE_PATTERN = re.compile(r"\s+")


def normalize_function_source(source: str, language: str) -> str:
    text = source
    text = BLOCK_COMMENT_PATTERN.sub(" ", text)
    text = LINE_COMMENT_PATTERN.sub(" ", text)
    text = WHITESPACE_PATTERN.sub(" ", text).strip()

    keywords = PYTHON_KEYWORDS if language == "python" else JS_KEYWORDS
    mapping: dict[str, str] = {}
    counter = 0

    def replace_identifier(match: re.Match[str]) -> str:
        nonlocal counter
        token = match.group(0)
        if token in keywords or token in BUILTINS:
            return token
        if token not in mapping:
            mapping[token] = f"var_{counter}"
            counter += 1
        return mapping[token]

    normalized = IDENTIFIER_PATTERN.sub(replace_identifier, text)
    return normalized.lower()
