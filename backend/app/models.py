from pydantic import BaseModel, Field


class DeadCodeSummary(BaseModel):
    unused_imports: int = 0
    unused_variables: int = 0
    unused_functions: int = 0


class DuplicateLogicSummary(BaseModel):
    duplicate_pairs: int = 0
    high_confidence_duplicates: int = 0
    medium_confidence_duplicates: int = 0
    possible_duplicates: int = 0


class ArchitectureSummary(BaseModel):
    god_files: int = 0
    hotspots: int = 0
    coupling_issues: int = 0
    circular_dependencies: int = 0


class DependencySummary(BaseModel):
    large_dependency_manifests: int = 0
    missing_manifests: int = 0
    concentration_issues: int = 0


class Scores(BaseModel):
    maintainability: int
    security: int
    architecture: int
    dead_code: int
    architecture_risk: int = 100


class Metrics(BaseModel):
    files_scanned: int
    total_lines: int
    python_files: int
    javascript_files: int
    typescript_files: int
    findings_count: int
    findings_by_category: dict[str, int] = Field(default_factory=dict)
    dead_code_summary: DeadCodeSummary = Field(default_factory=DeadCodeSummary)
    duplicate_logic_summary: DuplicateLogicSummary = Field(default_factory=DuplicateLogicSummary)
    architecture_summary: ArchitectureSummary = Field(default_factory=ArchitectureSummary)
    dependency_summary: DependencySummary = Field(default_factory=DependencySummary)


class AnalysisResponse(BaseModel):
    repository_name: str
    metrics: Metrics
    scores: Scores
    findings: list[dict]
    ai_report: str = ""
    prompt_export: str | None = None


class AiTestRequest(BaseModel):
    provider: str
    model: str | None = None
    api_key: str


class AiTestResponse(BaseModel):
    status: str
    message: str


class GitAnalyzeRequest(BaseModel):
    url: str = Field(min_length=1, max_length=500)
    branch: str | None = Field(default=None, max_length=200)
    token: str | None = Field(default=None, max_length=500)
