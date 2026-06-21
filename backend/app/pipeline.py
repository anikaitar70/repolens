import shutil
import tempfile
import zipfile
from pathlib import Path

from app.analysis_context import AnalysisContext
from app.analyzers.circular_import import detect_circular_imports
from app.analyzers.complexity import analyze_complexity
from app.analyzers.dead_code import analyze_dead_code
from app.analyzers.duplicate_logic import detect_duplicate_logic
from app.analyzers.large_file import detect_large_files
from app.analyzers.large_function import detect_large_functions
from app.analyzers.security import detect_security_issues
from app.config import settings
from app.exceptions import AnalysisError, InvalidUploadError, RepoLensError
from app.extract import safe_extract_zip
from app.gemini_client import generate_report
from app.logging_config import get_logger
from app.models import (
    AnalysisResponse,
    DeadCodeSummary,
    DuplicateLogicSummary,
    Metrics,
    Scores,
)
from app.scanner import compute_metrics, scan_repository
from app.scoring import compute_scores
from app.summary import (
    build_dead_code_summary,
    build_duplicate_logic_summary,
    build_findings_by_category,
    top_findings,
)

logger = get_logger(__name__)

IGNORED_ROOT_ENTRIES = {".DS_Store", "__MACOSX"}


def _list_root_entries(root: Path) -> list[Path]:
    return [p for p in root.iterdir() if p.name not in IGNORED_ROOT_ENTRIES]


def _extract_repository_name(extract_dir: Path, zip_name: str) -> str:
    entries = _list_root_entries(extract_dir)
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0].name
    return Path(zip_name).stem


def _resolve_repo_root(extract_dir: Path) -> Path:
    entries = _list_root_entries(extract_dir)
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return extract_dir


def analyze_zip(zip_path: Path, original_filename: str) -> AnalysisResponse:
    Path(settings.upload_directory).mkdir(parents=True, exist_ok=True)
    temp_dir = tempfile.mkdtemp(prefix="repolens_", dir=settings.upload_directory)

    try:
        extract_dir = Path(temp_dir)
        with zipfile.ZipFile(zip_path, "r") as archive:
            safe_extract_zip(archive, extract_dir)

        repo_root = _resolve_repo_root(extract_dir)
        repo_name = _extract_repository_name(extract_dir, original_filename)

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

        scores_dict = compute_scores(findings)
        dead_code_summary = build_dead_code_summary(findings)
        duplicate_logic_summary = build_duplicate_logic_summary(findings)
        findings_by_category = build_findings_by_category(findings)

        logger.info(
            "Running analyzers for %s: files=%d findings=%d duplicates=%s",
            repo_name,
            base_metrics["files_scanned"],
            len(findings),
            duplicate_logic_summary,
        )

        ai_report = generate_report(
            {
                **base_metrics,
                "findings_count": len(findings),
                "findings_by_category": findings_by_category,
                "dead_code_summary": dead_code_summary,
                "duplicate_logic_summary": duplicate_logic_summary,
            },
            scores_dict,
            findings,
            top_findings(findings),
        )

        return AnalysisResponse(
            repository_name=repo_name,
            metrics=Metrics(
                **base_metrics,
                findings_count=len(findings),
                findings_by_category=findings_by_category,
                dead_code_summary=DeadCodeSummary(**dead_code_summary),
                duplicate_logic_summary=DuplicateLogicSummary(**duplicate_logic_summary),
            ),
            scores=Scores(**scores_dict),
            findings=findings,
            ai_report=ai_report,
        )
    except (InvalidUploadError, zipfile.BadZipFile):
        raise
    except RepoLensError:
        raise
    except Exception as exc:
        logger.exception("Pipeline failure for %s", original_filename)
        raise AnalysisError("Repository analysis failed.") from exc
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
