import zipfile
from pathlib import Path

from app.config import settings
from app.exceptions import ZipSecurityError


def _is_safe_path(base_dir: Path, target_path: Path) -> bool:
    base_resolved = base_dir.resolve()
    target_resolved = target_path.resolve()
    return str(target_resolved).startswith(str(base_resolved))


def safe_extract_zip(archive: zipfile.ZipFile, target_dir: Path) -> None:
    """Extract ZIP archive with zip-slip and size protections."""
    target_dir.mkdir(parents=True, exist_ok=True)
    members = archive.infolist()

    if len(members) > settings.max_extracted_files:
        raise ZipSecurityError(
            f"Archive contains too many files (max {settings.max_extracted_files})."
        )

    total_uncompressed = 0
    for member in members:
        if member.is_dir():
            continue

        destination = target_dir / member.filename
        if not _is_safe_path(target_dir, destination):
            raise ZipSecurityError("Archive contains unsafe file paths (zip-slip detected).")

        total_uncompressed += member.file_size
        if total_uncompressed > settings.max_extracted_size:
            raise ZipSecurityError(
                f"Archive exceeds maximum extracted size ({settings.max_extracted_size} bytes)."
            )

    for member in members:
        destination = target_dir / member.filename
        if member.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            continue

        if not _is_safe_path(target_dir, destination):
            raise ZipSecurityError("Archive contains unsafe file paths (zip-slip detected).")

        destination.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(member) as source, destination.open("wb") as dest:
            dest.write(source.read())
