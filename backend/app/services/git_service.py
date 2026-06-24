"""Shallow git clone for public repository analysis."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from app.config import settings
from app.exceptions import InvalidUploadError, UploadLimitError
from app.logging_config import get_logger
from app.scanner import should_ignore_dir

logger = get_logger(__name__)

SSH_GIT_PATTERN = re.compile(r"^[\w.-]+@[\w.-]+:[\w./-]+\.git?$")


def _allowed_hosts() -> set[str]:
    return {
        host.strip().lower()
        for host in settings.allowed_git_hosts.split(",")
        if host.strip()
    }


def _is_blocked_host(hostname: str) -> bool:
    lowered = hostname.lower()
    if lowered in {"localhost", "127.0.0.1", "0.0.0.0"}:
        return True
    if lowered.endswith(".local"):
        return True
    # Basic private-network guard for literal IPs
    if re.match(r"^(10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)", lowered):
        return True
    return False


def normalize_git_url(url: str) -> tuple[str, str]:
    """Validate and normalize a git URL. Returns (clone_url, repo_name)."""
    cleaned = url.strip()
    if not cleaned:
        raise InvalidUploadError("Git repository URL is required.")

    if SSH_GIT_PATTERN.match(cleaned):
        raise InvalidUploadError(
            "SSH git URLs are not supported. Use an HTTPS URL "
            "(e.g. https://github.com/user/repo)."
        )

    if cleaned.startswith("git@"):
        raise InvalidUploadError(
            "SSH git URLs are not supported. Use an HTTPS URL "
            "(e.g. https://github.com/user/repo)."
        )

    if not cleaned.startswith(("http://", "https://")):
        cleaned = f"https://{cleaned}"

    parsed = urlparse(cleaned)
    if parsed.scheme != "https":
        raise InvalidUploadError("Only HTTPS git URLs are supported.")

    hostname = (parsed.hostname or "").lower()
    if not hostname or _is_blocked_host(hostname):
        raise InvalidUploadError("Invalid or unsupported git host.")

    allowed = _allowed_hosts()
    if hostname not in allowed and not any(
        hostname == host or hostname.endswith(f".{host}") for host in allowed
    ):
        supported = ", ".join(sorted(allowed))
        raise InvalidUploadError(
            f"Git host '{hostname}' is not allowed. Supported hosts: {supported}."
        )

    path = parsed.path.strip("/")
    if not path:
        raise InvalidUploadError("Repository path is missing from the git URL.")

    parts = [part for part in path.split("/") if part]
    if len(parts) < 2:
        raise InvalidUploadError("Git URL must include owner and repository name.")

    repo_name = parts[-1].removesuffix(".git")
    if not repo_name:
        raise InvalidUploadError("Could not determine repository name from URL.")

    clone_path = "/".join(parts)
    if not clone_path.endswith(".git"):
        clone_path = f"{clone_path}.git"

    clone_url = f"https://{hostname}/{clone_path}"
    return clone_url, repo_name


def _build_authenticated_url(clone_url: str, token: str | None) -> str:
    if not token:
        return clone_url
    parsed = urlparse(clone_url)
    return f"https://x-access-token:{token.strip()}@{parsed.hostname}{parsed.path}"


def _check_cloned_repo_size(root: Path) -> None:
    total_written = 0
    file_count = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not should_ignore_dir(d)]
        for filename in filenames:
            file_count += 1
            if file_count > settings.max_extracted_files:
                raise UploadLimitError(
                    f"Repository has too many files (>{settings.max_extracted_files}). "
                    "Try a smaller repository or a specific subdirectory."
                )

            file_path = Path(dirpath) / filename
            try:
                size = file_path.stat().st_size
            except OSError:
                continue

            if size > settings.max_single_file_size:
                raise UploadLimitError(
                    f"A file in the repository exceeds the maximum size "
                    f"({settings.max_single_file_size // (1024 * 1024)} MB per file)."
                )

            total_written += size
            if total_written > settings.max_extracted_size:
                raise UploadLimitError(
                    "Repository is too large. "
                    f"Maximum analyzed size is {settings.max_extracted_size // (1024 * 1024)} MB."
                )


def clone_repository(url: str, branch: str | None = None, token: str | None = None) -> Path:
    """Shallow-clone a public git repository into a temp directory."""
    clone_url, repo_name = normalize_git_url(url)
    authenticated_url = _build_authenticated_url(clone_url, token)

    work_dir = Path(tempfile.mkdtemp(prefix="repolens_git_", dir=settings.upload_directory))
    target = work_dir / repo_name

    command = [
        "git",
        "clone",
        "--depth",
        str(settings.git_clone_depth),
        "--single-branch",
    ]
    if branch and branch.strip():
        command.extend(["--branch", branch.strip()])
    command.extend([authenticated_url, str(target)])

    logger.info("Cloning repository: %s", clone_url)

    try:
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=settings.max_clone_seconds,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except subprocess.TimeoutExpired as exc:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise InvalidUploadError(
            f"Git clone timed out after {settings.max_clone_seconds} seconds."
        ) from exc
    except subprocess.CalledProcessError as exc:
        shutil.rmtree(work_dir, ignore_errors=True)
        stderr = (exc.stderr or "").strip()
        if "Authentication failed" in stderr or "could not read Username" in stderr:
            raise InvalidUploadError(
                "Could not access repository. It may be private — provide a personal access token."
            ) from exc
        if "not found" in stderr.lower() or "does not exist" in stderr.lower():
            raise InvalidUploadError("Repository not found. Check the URL and branch name.") from exc
        raise InvalidUploadError("Git clone failed. Check the URL and try again.") from exc
    except FileNotFoundError as exc:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise InvalidUploadError("Git is not available on the server.") from exc

    if not target.is_dir():
        shutil.rmtree(work_dir, ignore_errors=True)
        raise InvalidUploadError("Git clone completed but repository directory was not found.")

    _check_cloned_repo_size(target)
    return target
