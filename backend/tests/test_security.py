import io
import zipfile
from pathlib import Path

import pytest

from app.exceptions import ZipSecurityError
from app.extract import safe_extract_zip


def test_rejects_absolute_paths(tmp_path: Path):
    target = tmp_path / "extract"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("/etc/passwd", "malicious")

    buffer.seek(0)
    with zipfile.ZipFile(buffer, "r") as archive:
        with pytest.raises(ZipSecurityError, match="absolute"):
            safe_extract_zip(archive, target)


def test_rejects_path_traversal_in_name(tmp_path: Path):
    target = tmp_path / "extract"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("foo/../../evil.txt", "malicious")

    buffer.seek(0)
    with zipfile.ZipFile(buffer, "r") as archive:
        with pytest.raises(ZipSecurityError, match="traversal"):
            safe_extract_zip(archive, target)


def test_rejects_nested_archives(tmp_path: Path):
    target = tmp_path / "extract"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("nested.zip", b"PK")

    buffer.seek(0)
    with zipfile.ZipFile(buffer, "r") as archive:
        with pytest.raises(ZipSecurityError, match="Nested archive"):
            safe_extract_zip(archive, target)


def test_rejects_oversized_member(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from app.config import settings

    monkeypatch.setattr(settings, "max_single_file_size", 100)

    target = tmp_path / "extract"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        info = zipfile.ZipInfo("large.bin")
        info.file_size = 500
        archive.writestr(info, b"x" * 500)

    buffer.seek(0)
    with zipfile.ZipFile(buffer, "r") as archive:
        with pytest.raises(ZipSecurityError, match="maximum file size"):
            safe_extract_zip(archive, target)
