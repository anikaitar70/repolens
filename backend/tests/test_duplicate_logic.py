import io
import zipfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from app.analysis_context import AnalysisContext
from app.scoring import compute_scores
from app.services.code_normalizer import normalize_function_source
from app.services.embedding_service import EmbeddingService
from app.services.function_extractor import extract_functions
from app.services.similarity_engine import find_duplicate_pairs
from app.summary import build_duplicate_logic_summary


def test_normalize_equivalent_functions():
    source_a = """
def calculate_total(price, tax):
    total = price + tax
    if total < 0:
        return 0
    return total
"""
    source_b = """
def compute_amount(cost, vat):
    amount = cost + vat
    if amount < 0:
        return 0
    return amount
"""
    normalized_a = normalize_function_source(source_a, "python")
    normalized_b = normalize_function_source(source_b, "python")
    assert normalized_a == normalized_b


def test_cosine_similarity_identical_vectors():
    vector = [1.0, 0.0, 0.0]
    assert EmbeddingService.cosine_similarity(vector, vector) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors():
    vector_a = [1.0, 0.0]
    vector_b = [0.0, 1.0]
    assert EmbeddingService.cosine_similarity(vector_a, vector_b) == pytest.approx(0.0)


def test_function_extraction_python(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "orders.py").write_text(
        """
def process_order(order):
    if order.get("status") == "pending":
        return order.get("amount", 0) + 10
    return 0
""",
        encoding="utf-8",
    )

    ctx = AnalysisContext(project, [project / "orders.py"])
    functions = extract_functions(ctx)

    assert len(functions) == 1
    assert functions[0].name == "process_order"
    assert functions[0].line_count >= 4


def test_duplicate_detection_with_mocked_embeddings(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "a.py").write_text(
        """
def process_order(order):
    if order.get("status") == "pending":
        total = order.get("amount", 0) + 10
        if total > 100:
            return total * 0.9
        return total
    return 0
""",
        encoding="utf-8",
    )
    (project / "b.py").write_text(
        """
def handle_order(item):
    if item.get("status") == "pending":
        sum_value = item.get("amount", 0) + 10
        if sum_value > 100:
            return sum_value * 0.9
        return sum_value
    return 0
""",
        encoding="utf-8",
    )

    ctx = AnalysisContext(project, [project / "a.py", project / "b.py"])
    functions = extract_functions(ctx)
    normalized = {
        fn.id: normalize_function_source(fn.source, fn.language) for fn in functions
    }

    class MockEmbeddingService:
        def embed_batch(self, sources: list[str]) -> list[list[float]]:
            return [[1.0, 0.0, 0.0] for _ in sources]

        def cosine_similarity(self, a: list[float], b: list[float]) -> float:
            return EmbeddingService.cosine_similarity(a, b)

        @property
        def cache_size(self) -> int:
            return 2

    pairs = find_duplicate_pairs(functions, normalized, MockEmbeddingService())
    assert len(pairs) >= 1
    assert pairs[0].similarity >= 0.85


def test_scoring_v3_duplicate_penalties():
    findings = [
        {"type": "duplicate_logic", "confidence": "high"},
        {"type": "duplicate_logic", "confidence": "medium"},
        {"type": "duplicate_logic", "confidence": "low"},
    ]
    scores = compute_scores(findings)
    assert scores["maintainability"] == 93


def test_duplicate_logic_summary():
    findings = [
        {"type": "duplicate_logic", "confidence": "high"},
        {"type": "duplicate_logic", "confidence": "medium"},
        {"type": "duplicate_logic", "confidence": "low"},
    ]
    summary = build_duplicate_logic_summary(findings)
    assert summary["duplicate_pairs"] == 3
    assert summary["high_confidence_duplicates"] == 1


def test_api_includes_duplicate_summary():
    from fastapi.testclient import TestClient

    from app.main import app

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "dup/a.py",
            """
def alpha(x):
    if x > 0:
        return x * 2
    return 0
""",
        )
        archive.writestr(
            "dup/b.py",
            """
def beta(y):
    if y > 0:
        return y * 2
    return 0
""",
        )

    client = TestClient(app)

    with patch("app.analyzers.duplicate_logic.EmbeddingService") as mock_service:
        instance = mock_service.return_value
        instance.embed_batch.return_value = [[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]
        instance.cosine_similarity.side_effect = lambda a, b: EmbeddingService.cosine_similarity(a, b)
        instance.cache_size = 2

        response = client.post(
            "/api/analyze",
            files={"file": ("dup.zip", buffer.getvalue(), "application/zip")},
        )

    assert response.status_code == 200
    data = response.json()
    assert "duplicate_logic_summary" in data["metrics"]
