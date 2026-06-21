from __future__ import annotations

from app.analysis_context import AnalysisContext
from app.config import settings
from app.findings import create_finding
from app.logging_config import get_logger
from app.services.code_normalizer import normalize_function_source
from app.services.embedding_service import EmbeddingService
from app.services.function_extractor import extract_functions
from app.services.similarity_engine import find_duplicate_pairs

logger = get_logger(__name__)


def detect_duplicate_logic(ctx: AnalysisContext) -> list[dict]:
    if not settings.duplicate_detection_enabled:
        return []

    functions = extract_functions(ctx)
    if len(functions) < 2:
        return []

    normalized_sources = {
        fn.id: normalize_function_source(fn.source, fn.language) for fn in functions
    }

    embedding_service = EmbeddingService()
    pairs = find_duplicate_pairs(functions, normalized_sources, embedding_service)

    logger.info(
        "Duplicate detection: %d functions scanned, %d embeddings cached, %d pairs found",
        len(functions),
        embedding_service.cache_size,
        len(pairs),
    )

    findings: list[dict] = []
    for pair in pairs:
        fn_a = pair.function_a
        fn_b = pair.function_b
        severity = "high" if pair.confidence == "high" else "medium"

        finding = create_finding(
            type="duplicate_logic",
            severity=severity,
            category="maintainability",
            file=fn_a.file,
            line=fn_a.start_line,
            message=(
                f"Duplicate logic detected ({pair.similarity:.2f} similarity): "
                f"{fn_a.name} in {fn_a.file} ↔ {fn_b.name} in {fn_b.file}"
            ),
            confidence=pair.confidence,
            evidence={
                "file_a": fn_a.file,
                "function_a": fn_a.name,
                "file_b": fn_b.file,
                "function_b": fn_b.name,
                "similarity": pair.similarity,
                "start_line_a": fn_a.start_line,
                "start_line_b": fn_b.start_line,
            },
        )
        finding["file_a"] = fn_a.file
        finding["function_a"] = fn_a.name
        finding["file_b"] = fn_b.file
        finding["function_b"] = fn_b.name
        finding["similarity"] = pair.similarity
        findings.append(finding)

    return findings
