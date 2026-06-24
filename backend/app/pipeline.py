import shutil
import tempfile
import zipfile
from pathlib import Path

from app.analysis_context import AnalysisContext
from app.analyzers.architecture_intel import analyze_architecture
from app.analyzers.circular_import import detect_circular_imports
from app.analyzers.complexity import analyze_complexity
from app.analyzers.dead_code import analyze_dead_code
from app.analyzers.dependency_intel import analyze_dependencies
from app.analyzers.duplicate_logic import detect_duplicate_logic
from app.analyzers.large_file import detect_large_files
from app.analyzers.large_function import detect_large_functions
from app.analyzers.security import detect_security_issues
from app.config import settings
from app.exceptions import AnalysisError, InvalidUploadError, RepoLensError
from app.extract import safe_extract_zip
from app.logging_config import get_logger
from app.models import (
    AnalysisResponse,
    ArchitectureSummary,
    DeadCodeSummary,
    DependencySummary,
    DuplicateLogicSummary,
    Metrics,
    Scores,
)
from app.providers.factory import AiConfig
from app.scanner import compute_metrics, scan_repository
from app.scoring import compute_scores
from app.services.report_service import generate_report
from app.summary import (
    build_architecture_summary,
    build_dead_code_summary,
    build_dependency_summary,
    build_duplicate_logic_summary,
    build_findings_by_category,
    top_findings,
)

logger = get_logger(__name__)

IGNORED_ROOT_ENTRIES = {".DS_Store", "__MACOSX"}


def _list_root_entries(root: Path) -> list[Path]:
    return [p for p in root.iterdir() if p.name not in IGNORED_ROOT_ENTRIES]


def _extract_repository_name(extract_dir: Path, archive_name: str) -> str:
    entries = _list_root_entries(extract_dir)
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0].name
    return Path(archive_name).stem


def _resolve_repo_root(extract_dir: Path) -> Path:
    entries = _list_root_entries(extract_dir)
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return extract_dir


def analyze_repository(
    repo_root: Path,
    repo_name: str,
    ai_config: AiConfig | None = None,
) -> AnalysisResponse:
    files = scan_repository(repo_root)
    if not files:
        raise InvalidUploadError(
            "No supported source files found. Supported: Python, JavaScript, TypeScript."
        )

    base_metrics = compute_metrics(repo_root, files)
    ctx = AnalysisContext(repo_root, files)

    findings: list[dict] = []
    findings.extend(detect_large_files(ctx))
    findings.extend(detect_large_functions(ctx))
    findings.extend(analyze_complexity(ctx))
    findings.extend(detect_security_issues(ctx))
    findings.extend(detect_circular_imports(ctx))
    findings.extend(analyze_dead_code(ctx))
    findings.extend(detect_duplicate_logic(ctx))
    findings.extend(analyze_dependencies(ctx))
    findings.extend(analyze_architecture(ctx, findings))

    scores_dict = compute_scores(findings)
    dead_code_summary = build_dead_code_summary(findings)
    duplicate_logic_summary = build_duplicate_logic_summary(findings)
    architecture_summary = build_architecture_summary(findings)
    dependency_summary = build_dependency_summary(findings)
    findings_by_category = build_findings_by_category(findings)

    logger.info(
        "Running analyzers for %s: files=%d findings=%d architecture=%s",
        repo_name,
        base_metrics["files_scanned"],
        len(findings),
        architecture_summary,
    )

    metrics_payload = {
        **base_metrics,
        "findings_count": len(findings),
        "findings_by_category": findings_by_category,
        "dead_code_summary": dead_code_summary,
        "duplicate_logic_summary": duplicate_logic_summary,
        "architecture_summary": architecture_summary,
        "dependency_summary": dependency_summary,
    }

    report_result = generate_report(
        metrics_payload,
        scores_dict,
        findings,
        top_findings(findings),
        ai_config=ai_config,
    )

    return AnalysisResponse(
        repository_name=repo_name,
        metrics=Metrics(
            **base_metrics,
            findings_count=len(findings),
            findings_by_category=findings_by_category,
            dead_code_summary=DeadCodeSummary(**dead_code_summary),
            duplicate_logic_summary=DuplicateLogicSummary(**duplicate_logic_summary),
            architecture_summary=ArchitectureSummary(**architecture_summary),
            dependency_summary=DependencySummary(**dependency_summary),
        ),
        scores=Scores(**scores_dict),
        findings=findings,
        ai_report=report_result.ai_report,
        prompt_export=report_result.prompt_export,
    )


def analyze_directory(
    repo_dir: Path,
    repo_name: str,
    ai_config: AiConfig | None = None,
) -> AnalysisResponse:
    repo_root = _resolve_repo_root(repo_dir)
    resolved_name = repo_name if repo_root == repo_dir else repo_root.name
    return analyze_repository(repo_root, resolved_name, ai_config)


def analyze_zip(
    zip_path: Path,
    original_filename: str,
    ai_config: AiConfig | None = None,
) -> AnalysisResponse:
    Path(settings.upload_directory).mkdir(parents=True, exist_ok=True)
    temp_dir = tempfile.mkdtemp(prefix="repolens_", dir=settings.upload_directory)

    try:
        extract_dir = Path(temp_dir)
        with zipfile.ZipFile(zip_path, "r") as archive:
            safe_extract_zip(archive, extract_dir)

        repo_root = _resolve_repo_root(extract_dir)
        repo_name = _extract_repository_name(extract_dir, original_filename)
        return analyze_repository(repo_root, repo_name, ai_config)
    except (InvalidUploadError, zipfile.BadZipFile):
        raise
    except RepoLensError:
        raise
    except Exception as exc:
        logger.exception("Pipeline failure for %s", original_filename)
        raise AnalysisError("Repository analysis failed.") from exc
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
