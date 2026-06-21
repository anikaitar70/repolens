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
    assert len(data["findings"]) >= 1
    assert data["ai_report"]
