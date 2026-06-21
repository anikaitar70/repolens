import os
from pathlib import Path

IGNORED_DIRS = {
    "node_modules",
    ".git",
    "dist",
    "build",
    ".next",
    "coverage",
    "venv",
    "__pycache__",
}

SUPPORTED_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx"}


def should_ignore_dir(dirname: str) -> bool:
    return dirname in IGNORED_DIRS or dirname.startswith(".")


def scan_repository(root: Path) -> list[Path]:
    """Traverse repository and return supported source files."""
    files: list[Path] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not should_ignore_dir(d)]

        for filename in filenames:
            path = Path(dirpath) / filename
            if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(path)

    return sorted(files)


def count_lines(path: Path) -> int:
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        return len(content.splitlines())
    except OSError:
        return 0


def get_language(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".py":
        return "python"
    if ext in {".ts", ".tsx"}:
        return "typescript"
    return "javascript"


def compute_metrics(root: Path, files: list[Path]) -> dict:
    total_lines = sum(count_lines(f) for f in files)
    python_files = sum(1 for f in files if f.suffix.lower() == ".py")
    js_files = sum(1 for f in files if f.suffix.lower() in {".js", ".jsx"})
    ts_files = sum(1 for f in files if f.suffix.lower() in {".ts", ".tsx"})

    return {
        "files_scanned": len(files),
        "total_lines": total_lines,
        "python_files": python_files,
        "javascript_files": js_files,
        "typescript_files": ts_files,
    }


def relative_path(root: Path, path: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")
