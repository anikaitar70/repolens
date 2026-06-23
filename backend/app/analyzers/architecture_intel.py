"""Architecture intelligence: god files, coupling, and hotspots."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from app.analysis_context import AnalysisContext
from app.config import settings
from app.findings import create_finding
from app.services.dependency_graph import (
    build_combined_graph,
    module_name_from_path,
    module_to_display_path,
)


def _file_line_count(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
    except OSError:
        return 0


def _module_for_file(root: Path, path: Path) -> str:
    rel = path.relative_to(root).as_posix()
    return rel


def analyze_architecture(ctx: AnalysisContext, existing_findings: list[dict]) -> list[dict]:
    findings: list[dict] = []
    root = ctx.root
    graph = build_combined_graph(root, ctx.files)

    file_lines = {path: _file_line_count(path) for path in ctx.files}
    findings_by_file: dict[str, set[str]] = defaultdict(set)
    for finding in existing_findings:
        file_path = finding.get("file", "")
        if file_path:
            findings_by_file[file_path].add(finding.get("type", "unknown"))

    # God files: very large or large + high outgoing coupling
    for path in ctx.files:
        display = _module_for_file(root, path)
        lines = file_lines[path]
        try:
            module = module_name_from_path(root, path)
        except ValueError:
            continue
        fan_out = graph.fan_out(module)
        fan_in = graph.fan_in(module)

        is_god = lines >= settings.god_file_line_threshold
        if not is_god and lines >= settings.large_file_threshold and fan_out >= settings.high_coupling_threshold:
            is_god = True

        if is_god:
            findings.append(
                create_finding(
                    type="god_file",
                    severity="high" if lines >= settings.god_file_line_threshold else "medium",
                    category="architecture",
                    file=display,
                    line=0,
                    message=(
                        f"God file detected: {display} ({lines} lines"
                        f"{f', {fan_out} outgoing deps' if fan_out else ''})"
                    ),
                    evidence={"lines": lines, "fan_out": fan_out, "fan_in": fan_in, "issue": "God File"},
                )
            )

    # Highly coupled modules
    coupling_seen: set[str] = set()
    for module in graph.modules():
        fan_out = graph.fan_out(module)
        fan_in = graph.fan_in(module)
        is_python = any(
            module_name_from_path(root, file_path) == module
            for file_path in ctx.files
            if file_path.suffix == ".py"
        )
        display = module_to_display_path(module, is_python)

        if fan_out >= settings.high_coupling_threshold and display not in coupling_seen:
            coupling_seen.add(display)
            findings.append(
                create_finding(
                    type="high_coupling",
                    severity="medium",
                    category="architecture",
                    file=display,
                    line=0,
                    message=f"Highly coupled module: {display} imports {fan_out} other modules",
                    evidence={"fan_out": fan_out, "fan_in": fan_in, "issue": "High Coupling"},
                )
            )
        elif fan_in >= settings.high_coupling_threshold and display not in coupling_seen:
            coupling_seen.add(display)
            findings.append(
                create_finding(
                    type="high_coupling",
                    severity="medium",
                    category="architecture",
                    file=display,
                    line=0,
                    message=f"Highly coupled module: {display} is imported by {fan_in} other modules",
                    evidence={"fan_out": fan_out, "fan_in": fan_in, "issue": "High Coupling"},
                )
            )

    # Architectural hotspots: multiple distinct finding types in same file
    hotspot_types = {
        "large_file",
        "large_function",
        "complexity",
        "security",
        "unused_import",
        "unused_variable",
        "unused_function",
        "duplicate_logic",
        "god_file",
        "high_coupling",
    }
    for file_path, types in findings_by_file.items():
        relevant = types & hotspot_types
        if len(relevant) >= settings.hotspot_finding_threshold:
            findings.append(
                create_finding(
                    type="architectural_hotspot",
                    severity="high",
                    category="architecture",
                    file=file_path,
                    line=0,
                    message=(
                        f"Architectural hotspot: {file_path} has {len(relevant)} "
                        f"issue categories ({', '.join(sorted(relevant))})"
                    ),
                    evidence={
                        "issue": "Architectural Hotspot",
                        "finding_types": sorted(relevant),
                        "count": len(relevant),
                    },
                )
            )

    return findings
