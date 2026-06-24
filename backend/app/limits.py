"""Upload and extraction limit helpers."""

from __future__ import annotations

from app.config import settings


def format_bytes(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.0f} MB"
    if size >= 1024:
        return f"{size / 1024:.0f} KB"
    return f"{size} bytes"


def upload_too_large_message(actual_bytes: int) -> str:
    return (
        f"Upload is too large ({format_bytes(actual_bytes)}). "
        f"Maximum ZIP size is {format_bytes(settings.max_upload_size)}. "
        "Try uploading a smaller archive or exclude build folders (node_modules, .git, dist)."
    )


def get_public_limits() -> dict:
    return {
        "max_upload_bytes": settings.max_upload_size,
        "max_upload_label": format_bytes(settings.max_upload_size),
        "max_extracted_bytes": settings.max_extracted_size,
        "max_extracted_label": format_bytes(settings.max_extracted_size),
        "max_extracted_files": settings.max_extracted_files,
        "max_single_file_bytes": settings.max_single_file_size,
        "max_single_file_label": format_bytes(settings.max_single_file_size),
    }
