from __future__ import annotations

from pathlib import Path

from app.services.ast_parser import ASTParser, ParsedFile


class AnalysisContext:
    """Shared analysis state: file index and cached ASTs."""

    def __init__(self, root: Path, files: list[Path]) -> None:
        self.root = root
        self.files = files
        self.ast = ASTParser()
        self._parsed: list[ParsedFile] | None = None

    def rel_path(self, file_path: Path) -> str:
        return str(file_path.relative_to(self.root)).replace("\\", "/")

    def get_parsed_files(self) -> list[ParsedFile]:
        if self._parsed is None:
            self._parsed = self.ast.parse_files(self.root, self.files)
        return self._parsed

    def get_parsed(self, file_path: Path) -> ParsedFile | None:
        return self.ast.parse_file(self.root, file_path)
