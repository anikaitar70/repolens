from typing import Any

from pydantic import BaseModel, Field


class DeadCodeSummary(BaseModel):
    unused_imports: int = 0
    unused_variables: int = 0
    unused_functions: int = 0


class Scores(BaseModel):
    maintainability: int
    security: int
    architecture: int
    dead_code: int


class Metrics(BaseModel):
    files_scanned: int
    total_lines: int
    python_files: int
    javascript_files: int
    typescript_files: int
    findings_count: int
    findings_by_category: dict[str, int] = Field(default_factory=dict)
    dead_code_summary: DeadCodeSummary = Field(default_factory=DeadCodeSummary)


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
    top_findings: list[dict[str, Any]]
