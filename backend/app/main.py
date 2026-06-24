import concurrent.futures
import tempfile
import zipfile
from pathlib import Path

from fastapi import FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.exceptions import RepoLensError
from app.logging_config import get_logger, setup_logging
from app.models import AiTestRequest, AiTestResponse, AnalysisResponse
from app.pipeline import analyze_zip
from app.limits import get_public_limits, upload_too_large_message
from app.providers.factory import AiConfig
from app.services.report_service import verify_ai_connection

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="RepoLens API",
    description="AI-assisted repository audit platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RepoLensError)
async def repolens_error_handler(_request: Request, exc: RepoLensError) -> JSONResponse:
    logger.warning("Request failed: %s", exc.message)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/limits")
async def limits() -> dict:
    return get_public_limits()


def _parse_ai_config(
    provider: str | None,
    model: str | None,
    api_key: str | None,
) -> AiConfig | None:
    if not provider and not api_key:
        return None
    return AiConfig(
        provider=provider.strip().lower() if provider else None,
        model=model.strip() if model else None,
        api_key=api_key.strip() if api_key else None,
    )


def _run_analysis_with_timeout(
    zip_path: Path,
    filename: str,
    ai_config: AiConfig | None,
) -> AnalysisResponse:
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(analyze_zip, zip_path, filename, ai_config)
        return future.result(timeout=settings.max_analysis_seconds)


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(
    file: UploadFile = File(...),
    x_ai_provider: str | None = Header(default=None, alias="X-AI-Provider"),
    x_ai_model: str | None = Header(default=None, alias="X-AI-Model"),
    x_ai_api_key: str | None = Header(default=None, alias="X-AI-Api-Key"),
) -> AnalysisResponse:
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only ZIP files are supported.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(content) > settings.max_upload_size:
        raise HTTPException(
            status_code=413,
            detail=upload_too_large_message(len(content)),
        )

    upload_dir = Path(settings.upload_directory)
    upload_dir.mkdir(parents=True, exist_ok=True)

    ai_config = _parse_ai_config(x_ai_provider, x_ai_model, x_ai_api_key)
    # Never log API keys — only provider name when present
    if ai_config and ai_config.provider:
        logger.info(
            "Analysis started for upload: %s (BYOK provider=%s)",
            file.filename,
            ai_config.provider,
        )
    else:
        logger.info("Analysis started for upload: %s", file.filename)

    with tempfile.NamedTemporaryFile(
        suffix=".zip", delete=False, dir=upload_dir
    ) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        result = _run_analysis_with_timeout(tmp_path, file.filename, ai_config)
        logger.info(
            "Analysis completed for %s: %d findings",
            result.repository_name,
            len(result.findings),
        )
        return result
    except concurrent.futures.TimeoutError:
        logger.warning("Analysis timed out for upload: %s", file.filename)
        raise HTTPException(
            status_code=504,
            detail=f"Analysis exceeded time limit of {settings.max_analysis_seconds} seconds.",
        ) from None
    except zipfile.BadZipFile:
        logger.warning("Invalid ZIP upload: %s", file.filename)
        raise HTTPException(status_code=400, detail="Invalid ZIP file.") from None
    except RepoLensError:
        raise
    except Exception:
        logger.exception("Analysis failed for upload: %s", file.filename)
        detail = "Analysis failed due to an internal error."
        if settings.debug:
            raise
        raise HTTPException(status_code=500, detail=detail) from None
    finally:
        tmp_path.unlink(missing_ok=True)


@app.post("/api/ai/test", response_model=AiTestResponse)
async def test_ai(body: AiTestRequest) -> AiTestResponse:
    ai_config = AiConfig(
        provider=body.provider,
        model=body.model,
        api_key=body.api_key,
    )
    status, message = verify_ai_connection(ai_config)
    return AiTestResponse(status=status, message=message)
