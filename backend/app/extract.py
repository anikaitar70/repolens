import zipfile
from pathlib import Path, PurePosixPath

from app.config import settings
from app.exceptions import UploadLimitError, ZipSecurityError

NESTED_ARCHIVE_EXTENSIONS = {".zip", ".tar", ".gz", ".tgz", ".bz2", ".7z", ".rar"}
READ_CHUNK_SIZE = 64 * 1024


def _is_safe_path(base_dir: Path, target_path: Path) -> bool:
    """Verify target resolves inside base_dir (zip-slip protection)."""
    base_resolved = base_dir.resolve()
    target_resolved = target_path.resolve()
    try:
        target_resolved.relative_to(base_resolved)
    except ValueError:
        return False
    return True


def _normalize_member_name(name: str) -> str:
    normalized = name.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _reject_unsafe_member_name(name: str) -> None:
    if not name or name.endswith("/"):
        return

    if name.startswith("/") or name.startswith("\\"):
        raise ZipSecurityError("Archive contains absolute file paths.")

    if PurePosixPath(name).is_absolute():
        raise ZipSecurityError("Archive contains absolute file paths.")

    if ".." in PurePosixPath(name).parts:
        raise ZipSecurityError("Archive contains path traversal sequences.")

    suffix = PurePosixPath(name).suffix.lower()
    if suffix in NESTED_ARCHIVE_EXTENSIONS:
        raise ZipSecurityError("Nested archive files are not allowed.")


def safe_extract_zip(archive: zipfile.ZipFile, target_dir: Path) -> None:
    """Extract ZIP archive with zip-slip, size, and nested-archive protections."""
    target_dir.mkdir(parents=True, exist_ok=True)
    members = archive.infolist()

    if len(members) > settings.max_extracted_files:
        raise UploadLimitError(
            f"Repository has too many files ({len(members)}). "
            f"Maximum is {settings.max_extracted_files}. "
            "Exclude dependencies and build output before zipping."
        )

    declared_uncompressed = 0
    for member in members:
        member_name = _normalize_member_name(member.filename)
        _reject_unsafe_member_name(member_name)

        if member.is_dir():
            destination = target_dir / member_name
            if not _is_safe_path(target_dir, destination):
                raise ZipSecurityError("Archive contains unsafe file paths (zip-slip detected).")
            continue

        destination = target_dir / member_name
        if not _is_safe_path(target_dir, destination):
            raise ZipSecurityError("Archive contains unsafe file paths (zip-slip detected).")

        if member.file_size > settings.max_single_file_size:
            raise UploadLimitError(
                f"A file in the archive exceeds the maximum size "
                f"({settings.max_single_file_size // (1024 * 1024)} MB per file)."
            )

        declared_uncompressed += member.file_size
        if declared_uncompressed > settings.max_extracted_size:
            raise UploadLimitError(
                "Repository is too large when extracted. "
                f"Maximum extracted size is {settings.max_extracted_size // (1024 * 1024)} MB. "
                "Remove node_modules, .git, dist, or other generated folders."
            )

    total_written = 0
    for member in members:
        member_name = _normalize_member_name(member.filename)
        destination = target_dir / member_name

        if member.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            continue

        if not _is_safe_path(target_dir, destination):
            raise ZipSecurityError("Archive contains unsafe file paths (zip-slip detected).")

        destination.parent.mkdir(parents=True, exist_ok=True)
        file_written = 0

        with archive.open(member) as source, destination.open("wb") as dest:
            while True:
                chunk = source.read(READ_CHUNK_SIZE)
                if not chunk:
                    break

                file_written += len(chunk)
                total_written += len(chunk)

                if file_written > settings.max_single_file_size:
                    destination.unlink(missing_ok=True)
                    raise UploadLimitError(
                        f"A file in the archive exceeds the maximum size "
                        f"({settings.max_single_file_size // (1024 * 1024)} MB per file)."
                    )

                if total_written > settings.max_extracted_size:
                    destination.unlink(missing_ok=True)
                    raise UploadLimitError(
                        "Repository is too large when extracted. "
                        f"Maximum extracted size is {settings.max_extracted_size // (1024 * 1024)} MB. "
                        "Remove node_modules, .git, dist, or other generated folders."
                    )

                dest.write(chunk)
