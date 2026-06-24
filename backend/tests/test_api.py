import io
import zipfile

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_rejects_non_zip():
    response = client.post(
        "/api/analyze",
        files={"file": ("repo.txt", b"not a zip", "text/plain")},
    )
    assert response.status_code == 400
    assert "ZIP" in response.json()["detail"]


def test_analyze_rejects_empty_zip():
    response = client.post(
        "/api/analyze",
        files={"file": ("empty.zip", b"", "application/zip")},
    )
    assert response.status_code == 400


def test_limits_endpoint():
    from app.config import settings

    response = client.get("/api/limits")
    assert response.status_code == 200
    data = response.json()
    assert data["max_upload_bytes"] == settings.max_upload_size
    assert "max_upload_label" in data


def test_analyze_rejects_oversized_upload(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "max_upload_size", 100)

    response = client.post(
        "/api/analyze",
        files={"file": ("big.zip", b"x" * 200, "application/zip")},
    )
    assert response.status_code == 413
    assert "too large" in response.json()["detail"].lower()


def test_analyze_git_rejects_invalid_url():
    response = client.post(
        "/api/analyze/git",
        json={"url": "https://evil.example.com/user/repo.git"},
    )
    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"].lower()


def test_analyze_valid_python_repo():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "project/main.py",
            'API_KEY = "secret-key-12345678"\n\ndef run():\n    return eval("1")\n',
        )

    response = client.post(
        "/api/analyze",
        files={"file": ("project.zip", buffer.getvalue(), "application/zip")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["repository_name"] == "project"
    assert data["metrics"]["files_scanned"] == 1
    assert data["scores"]["security"] < 100
    assert "dead_code" in data["scores"]
    assert "findings_by_category" in data["metrics"]
    assert "dead_code_summary" in data["metrics"]
    assert len(data["findings"]) >= 1
    assert "id" in data["findings"][0]
    assert "category" in data["findings"][0]
    assert data["ai_report"]
