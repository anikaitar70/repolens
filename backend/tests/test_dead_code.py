from pathlib import Path

from app.analysis_context import AnalysisContext
from app.analyzers.dead_code import analyze_dead_code
from app.findings import create_finding
from app.scoring import compute_scores
from app.summary import build_dead_code_summary


def test_compute_scores_v2_includes_dead_code():
    findings = [
        {"type": "unused_import"},
        {"type": "unused_variable"},
        {"type": "unused_function"},
        {"type": "circular_dependency"},
    ]
    scores = compute_scores(findings)

    assert scores["dead_code"] == 94
    assert scores["architecture"] == 95


def test_create_finding_has_required_fields():
    finding = create_finding(
        type="unused_import",
        severity="low",
        category="dead_code",
        file="utils.py",
        line=3,
        message="Import 'numpy' is never used",
        confidence="high",
        evidence={"symbol": "numpy"},
    )

    assert finding["type"] == "unused_import"
    assert finding["category"] == "dead_code"
    assert finding["id"]
    assert finding["message"]


def test_dead_code_summary_counts(tmp_path: Path):
    findings = [
        {"type": "unused_import"},
        {"type": "unused_import"},
        {"type": "unused_variable"},
        {"type": "unused_function"},
    ]
    summary = build_dead_code_summary(findings)

    assert summary == {
        "unused_imports": 2,
        "unused_variables": 1,
        "unused_functions": 1,
    }


def test_unused_import_detection(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "utils.py").write_text(
        "import json\nimport numpy\n\ndef run():\n    return json.dumps({'ok': True})\n",
        encoding="utf-8",
    )

    ctx = AnalysisContext(project, [project / "utils.py"])
    findings = analyze_dead_code(ctx)
    import_findings = [f for f in findings if f["type"] == "unused_import"]

    assert any(f["evidence"]["symbol"] == "numpy" for f in import_findings)
    assert not any(f["evidence"]["symbol"] == "json" for f in import_findings)


def test_unused_variable_detection(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "example.ts").write_text(
        "const temp = 123;\nconst active = true;\nconsole.log(active);\n",
        encoding="utf-8",
    )

    ctx = AnalysisContext(project, [project / "example.ts"])
    findings = analyze_dead_code(ctx)
    variable_findings = [f for f in findings if f["type"] == "unused_variable"]

    assert any(f["evidence"]["variable"] == "temp" for f in variable_findings)


def test_unused_function_detection(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "helpers.py").write_text(
        "def format_date():\n    return '2026-01-01'\n\ndef main():\n    print('ok')\n",
        encoding="utf-8",
    )

    ctx = AnalysisContext(project, [project / "helpers.py"])
    findings = analyze_dead_code(ctx)
    function_findings = [f for f in findings if f["type"] == "unused_function"]

    assert any(f["evidence"]["function"] == "format_date" for f in function_findings)
    assert not any(f["evidence"]["function"] == "main" for f in function_findings)
