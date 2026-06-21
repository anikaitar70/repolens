from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterator

from tree_sitter import Language, Node, Parser, Tree

from app.logging_config import get_logger
from app.scanner import get_language

logger = get_logger(__name__)


@dataclass(frozen=True)
class ParsedFile:
    path: Path
    rel_path: str
    language: str
    source: bytes
    text: str
    tree: Tree


def _node_text(source: bytes, node: Node) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="ignore")


class ASTParser:
    """Parse source files once and cache ASTs for reuse across analyzers."""

    def __init__(self) -> None:
        self._cache: dict[str, ParsedFile] = {}
        self._parsers: dict[str, Parser] = {}

    @staticmethod
    @lru_cache(maxsize=3)
    def _load_language(language: str) -> Language | None:
        try:
            if language == "python":
                import tree_sitter_python as tspython

                return Language(tspython.language())
            if language in {"javascript", "typescript"}:
                import tree_sitter_javascript as tsjavascript

                return Language(tsjavascript.language())
        except Exception:
            logger.exception("Failed to load tree-sitter grammar for %s", language)
            return None
        return None

    def _get_parser(self, language: str) -> Parser | None:
        if language in self._parsers:
            return self._parsers[language]

        grammar = self._load_language(language)
        if grammar is None:
            return None

        parser = Parser(grammar)
        self._parsers[language] = parser
        return parser

    def parse_file(self, root: Path, file_path: Path) -> ParsedFile | None:
        cache_key = str(file_path.resolve())
        if cache_key in self._cache:
            return self._cache[cache_key]

        language = get_language(file_path)
        parser = self._get_parser(language)
        if parser is None:
            return None

        try:
            source = file_path.read_bytes()
            text = source.decode("utf-8", errors="ignore")
            tree = parser.parse(source)
        except OSError:
            logger.warning("Unable to read file for AST parsing: %s", file_path)
            return None

        rel_path = str(file_path.relative_to(root)).replace("\\", "/")
        parsed = ParsedFile(
            path=file_path,
            rel_path=rel_path,
            language=language,
            source=source,
            text=text,
            tree=tree,
        )
        self._cache[cache_key] = parsed
        return parsed

    def parse_files(self, root: Path, files: list[Path]) -> list[ParsedFile]:
        parsed_files: list[ParsedFile] = []
        for file_path in files:
            parsed = self.parse_file(root, file_path)
            if parsed is not None:
                parsed_files.append(parsed)
        return parsed_files

    @staticmethod
    def walk(node: Node) -> Iterator[Node]:
        stack = [node]
        while stack:
            current = stack.pop()
            yield current
            for index in range(current.child_count - 1, -1, -1):
                child = current.child(index)
                if child is not None:
                    stack.append(child)

    @staticmethod
    def node_text(parsed: ParsedFile, node: Node) -> str:
        return _node_text(parsed.source, node)

    @staticmethod
    def line_number(parsed: ParsedFile, node: Node) -> int:
        return node.start_point[0] + 1
