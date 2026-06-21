import tempfile
import zipfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.exceptions import RepoLensError
from app.logging_config import get_logger, setup_logging
from app.models import AnalysisResponse
from app.pipeline import analyze_zip

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


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(file: UploadFile = File(...)) -> AnalysisResponse:
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only ZIP files are supported.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(content) > settings.max_upload_size:
        raise HTTPException(
            status_code=413,
            detail=f"Upload exceeds maximum size of {settings.max_upload_size} bytes.",
        )

    upload_dir = Path(settings.upload_directory)
    upload_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Analysis started for upload: %s", file.filename)

    with tempfile.NamedTemporaryFile(
        suffix=".zip", delete=False, dir=upload_dir
    ) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        result = analyze_zip(tmp_path, file.filename)
        logger.info(
            "Analysis completed for %s: %d findings",
            result.repository_name,
            len(result.findings),
        )
        return result
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
