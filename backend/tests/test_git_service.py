import pytest

from app.exceptions import InvalidUploadError
from app.services.git_service import normalize_git_url


def test_normalize_github_https_url():
    clone_url, repo_name = normalize_git_url("https://github.com/octocat/Hello-World")
    assert clone_url == "https://github.com/octocat/Hello-World.git"
    assert repo_name == "Hello-World"


def test_normalize_github_url_without_scheme():
    clone_url, repo_name = normalize_git_url("github.com/octocat/Hello-World.git")
    assert clone_url == "https://github.com/octocat/Hello-World.git"
    assert repo_name == "Hello-World"


def test_rejects_ssh_url():
    with pytest.raises(InvalidUploadError, match="SSH"):
        normalize_git_url("git@github.com:octocat/Hello-World.git")


def test_rejects_unsupported_host():
    with pytest.raises(InvalidUploadError, match="not allowed"):
        normalize_git_url("https://example.com/user/repo.git")
