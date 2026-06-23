from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.analyzers.architecture_intel import analyze_architecture
from app.analyzers.dependency_intel import analyze_dependencies
from app.analysis_context import AnalysisContext
from app.main import app
from app.providers.factory import AiConfig, get_report_provider
from app.scoring import compute_scores
from app.services.report_service import build_prompt_export, generate_report, verify_ai_connection
from app.summary import build_architecture_summary, build_dependency_summary


def test_get_report_provider_byok():
    config = AiConfig(provider="groq", model="llama-3.3-70b-versatile", api_key="test-key")
    provider = get_report_provider(config)
    assert provider is not None
    assert provider.name == "groq"


def test_prompt_export_when_no_api_key():
    metrics = {
        "files_scanned": 1,
        "total_lines": 10,
        "findings_by_category": {},
        "dead_code_summary": {},
        "duplicate_logic_summary": {},
        "architecture_summary": {},
        "dependency_summary": {},
    }
    scores = {
        "maintainability": 100,
        "security": 100,
        "architecture": 100,
        "dead_code": 100,
        "architecture_risk": 100,
    }

    with patch("app.services.report_service.get_report_provider", return_value=None):
        result = generate_report(metrics, scores, [], [])

    assert result.ai_report == ""
    assert result.prompt_export is not None
    assert "Executive Summary" in result.prompt_export


def test_generate_report_with_mock_provider():
    provider = MagicMock()
    provider.name = "groq"
    provider.generate.return_value = "# Report\n\n## Executive Summary"

    metrics = {
        "files_scanned": 1,
        "total_lines": 10,
        "findings_by_category": {},
        "dead_code_summary": {},
        "duplicate_logic_summary": {},
        "architecture_summary": {},
        "dependency_summary": {},
    }
    scores = {
        "maintainability": 90,
        "security": 90,
        "architecture": 90,
        "dead_code": 90,
        "architecture_risk": 90,
    }

    with patch("app.services.report_service.get_report_provider", return_value=provider):
        result = generate_report(metrics, scores, [], [])

    assert result.ai_report.startswith("# Report")
    assert result.prompt_export is None


def test_architecture_risk_scoring():
    findings = [
        {"type": "circular_dependency"},
        {"type": "god_file", "severity": "high"},
        {"type": "architectural_hotspot"},
        {"type": "high_coupling"},
    ]
    scores = compute_scores(findings)
    assert scores["architecture_risk"] == 72


def test_dependency_intel_missing_manifest(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "main.py").write_text("print('hello')\n", encoding="utf-8")

    ctx = AnalysisContext(project, [project / "main.py"])
    findings = analyze_dependencies(ctx)

    assert any(f["type"] == "missing_dependency_file" for f in findings)


def test_architecture_hotspot_detection(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    target = project / "hotspot.py"
    target.write_text("x = 1\n" * 600, encoding="utf-8")

    existing = [
        {
            "type": "large_file",
            "category": "maintainability",
            "file": "hotspot.py",
            "severity": "high",
        },
        {
            "type": "complexity",
            "category": "maintainability",
            "file": "hotspot.py",
            "severity": "medium",
        },
        {
            "type": "security",
            "category": "security",
            "file": "hotspot.py",
            "severity": "high",
        },
    ]

    ctx = AnalysisContext(project, [target])
    findings = analyze_architecture(ctx, existing)

    assert any(f["type"] == "architectural_hotspot" for f in findings)


def test_ai_test_endpoint_invalid_key():
    client = TestClient(app)

    with patch(
        "app.services.report_service.verify_ai_connection",
        return_value=("invalid", "Invalid API key."),
    ):
        result = client.post(
            "/api/ai/test",
            json={"provider": "groq", "model": "llama-3.3-70b-versatile", "api_key": "bad"},
        )

    assert result.status_code == 200
    assert result.json()["status"] == "invalid"


def test_analyze_returns_prompt_export_without_key():
    import io
    import zipfile

    client = TestClient(app)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("sample/main.py", "print('hello')\n")

    with patch("app.services.report_service.get_report_provider", return_value=None):
        response = client.post(
            "/api/analyze",
            files={"file": ("sample.zip", buffer.getvalue(), "application/zip")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["prompt_export"]
    assert data["ai_report"] == ""


def test_architecture_and_dependency_summaries():
    findings = [
        {"type": "god_file"},
        {"type": "architectural_hotspot"},
        {"type": "high_coupling"},
        {"type": "circular_dependency"},
        {"type": "large_dependency_count"},
        {"type": "missing_dependency_file"},
    ]
    arch = build_architecture_summary(findings)
    dep = build_dependency_summary(findings)

    assert arch["god_files"] == 1
    assert arch["hotspots"] == 1
    assert dep["large_dependency_manifests"] == 1


def test_build_prompt_export_includes_summaries():
    prompt = build_prompt_export(
        {
            "architecture_summary": {"god_files": 2},
            "dependency_summary": {"missing_manifests": 1},
            "dead_code_summary": {},
            "duplicate_logic_summary": {},
            "findings_by_category": {},
        },
        {"architecture_risk": 80},
        [],
        [],
    )
    assert "architecture_summary" in prompt
    assert "dependency_summary" in prompt


def test_groq_connection_test_success():
    config = AiConfig(provider="groq", model="llama-3.3-70b-versatile", api_key="test")
    response = httpx.Response(
        200,
        json={"choices": [{"message": {"content": "connected"}}]},
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
    )

    with patch("httpx.Client.post", return_value=response):
        status, message = verify_ai_connection(config)

    assert status == "connected"
