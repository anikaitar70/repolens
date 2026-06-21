from __future__ import annotations

from dataclasses import dataclass

from app.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.function_extractor import ExtractedFunction


@dataclass(frozen=True)
class DuplicatePair:
    function_a: ExtractedFunction
    function_b: ExtractedFunction
    similarity: float
    confidence: str


def _is_trivial_function(function: ExtractedFunction) -> bool:
    if function.line_count < settings.duplicate_min_lines:
        return True

    name = function.name.lower()
    if name.startswith(("get_", "get", "set_", "set", "is_", "is")) and function.line_count <= 3:
        return True

    if len(function.source.strip().splitlines()) <= 2:
        return True

    return False


def _confidence_label(similarity: float) -> str | None:
    if similarity >= settings.duplicate_high_threshold:
        return "high"
    if similarity >= settings.duplicate_medium_threshold:
        return "medium"
    if similarity >= settings.duplicate_possible_threshold:
        return "low"
    return None


def _length_bucket(line_count: int) -> int:
    return line_count // settings.duplicate_length_bucket_size


def _compare_pair(
    fn_a: ExtractedFunction,
    emb_a: list[float],
    fn_b: ExtractedFunction,
    emb_b: list[float],
    seen_pairs: set[tuple[str, str]],
    pairs: list[DuplicatePair],
) -> None:
    if fn_a.id == fn_b.id:
        return
    if fn_a.file == fn_b.file and fn_a.name == fn_b.name:
        return

    pair_key = tuple(sorted((fn_a.id, fn_b.id)))
    if pair_key in seen_pairs:
        return

    similarity = EmbeddingService.cosine_similarity(emb_a, emb_b)
    confidence = _confidence_label(similarity)
    if confidence is None:
        return

    seen_pairs.add(pair_key)
    pairs.append(
        DuplicatePair(
            function_a=fn_a,
            function_b=fn_b,
            similarity=round(similarity, 4),
            confidence=confidence,
        )
    )


def find_duplicate_pairs(
    functions: list[ExtractedFunction],
    normalized_sources: dict[str, str],
    embedding_service: EmbeddingService,
) -> list[DuplicatePair]:
    """
    Performance approach:
    - Skip trivial / tiny functions
    - Cap total functions analyzed
    - Bucket by line-count to reduce comparison space
    - Compare within bucket and adjacent buckets only
    - Cache embeddings by normalized source hash
    """
    eligible = [fn for fn in functions if not _is_trivial_function(fn)]
    eligible.sort(key=lambda fn: fn.line_count, reverse=True)
    eligible = eligible[: settings.duplicate_max_functions]

    if len(eligible) < 2:
        return []

    normalized_list = [normalized_sources[fn.id] for fn in eligible]
    embeddings = embedding_service.embed_batch(normalized_list)
    indexed = list(zip(eligible, embeddings, strict=True))

    buckets: dict[int, list[tuple[ExtractedFunction, list[float]]]] = {}
    for function, embedding in indexed:
        bucket = _length_bucket(function.line_count)
        buckets.setdefault(bucket, []).append((function, embedding))

    pairs: list[DuplicatePair] = []
    seen_pairs: set[tuple[str, str]] = set()
    bucket_keys = sorted(buckets.keys())

    for key in bucket_keys:
        group = buckets[key]
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                _compare_pair(group[i][0], group[i][1], group[j][0], group[j][1], seen_pairs, pairs)

        if key + 1 in buckets:
            next_group = buckets[key + 1]
            for fn_a, emb_a in group:
                for fn_b, emb_b in next_group:
                    _compare_pair(fn_a, emb_a, fn_b, emb_b, seen_pairs, pairs)

    pairs.sort(key=lambda pair: pair.similarity, reverse=True)
    return pairs[: settings.duplicate_max_pairs]
