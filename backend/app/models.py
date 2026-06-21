from typing import Any

from pydantic import BaseModel, Field


class Scores(BaseModel):
    maintainability: int
    security: int
    architecture: int


class Metrics(BaseModel):
    files_scanned: int
    total_lines: int
    python_files: int
    javascript_files: int
    typescript_files: int
    findings_count: int


class AnalysisResponse(BaseModel):
    repository_name: str
    metrics: Metrics
    scores: Scores
    findings: list[dict[str, Any]]
    ai_report: str


class GeminiPayload(BaseModel):
    metrics: dict[str, Any]
    scores: dict[str, int]
    findings: list[dict[str, Any]]
