import io
import zipfile
from pathlib import Path

import pytest

from app.exceptions import ZipSecurityError
from app.extract import safe_extract_zip
from app.scoring import compute_scores


def test_compute_scores_applies_deductions():
    findings = [
        {"type": "large_file"},
        {"type": "large_function"},
        {"type": "complexity"},
        {"type": "security"},
        {"type": "circular_dependency"},
    ]
    scores = compute_scores(findings)

    assert scores["maintainability"] == 90
    assert scores["security"] == 90
    assert scores["architecture"] == 95
    assert scores["dead_code"] == 100


def test_compute_scores_clamps_at_zero():
    findings = [{"type": "security"}] * 15
    scores = compute_scores(findings)
    assert scores["security"] == 0


def test_safe_extract_rejects_zip_slip(tmp_path: Path):
    target = tmp_path / "extract"
    target.mkdir()

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        info = zipfile.ZipInfo("../evil.txt")
        archive.writestr(info, "malicious")

    buffer.seek(0)
    with zipfile.ZipFile(buffer, "r") as archive:
        with pytest.raises(ZipSecurityError, match="traversal|zip-slip"):
            safe_extract_zip(archive, target)


def test_safe_extract_allows_valid_archive(tmp_path: Path):
    target = tmp_path / "extract"

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("src/main.py", "print('hello')")

    buffer.seek(0)
    with zipfile.ZipFile(buffer, "r") as archive:
        safe_extract_zip(archive, target)

    assert (target / "src" / "main.py").exists()
