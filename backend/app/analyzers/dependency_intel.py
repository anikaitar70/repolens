"""Dependency manifest intelligence for package.json, requirements.txt, pyproject.toml."""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.analysis_context import AnalysisContext
from app.config import settings
from app.findings import create_finding
from app.scanner import scan_manifest_files

REQUIREMENTS_PATTERN = re.compile(
    r"^[A-Za-z0-9_\-\.]+(?:\[[^\]]+\])?(?:[><=!~]=[^\s,;]+)?",
    re.MULTILINE,
)


def _parse_requirements(content: str) -> list[str]:
    packages: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("-"):
            continue
        match = REQUIREMENTS_PATTERN.match(stripped)
        if match:
            name = re.split(r"[<>=!\[;]", match.group(0))[0].strip()
            if name:
                packages.append(name.lower())
    return packages


def _parse_pyproject(content: str) -> list[str]:
    packages: list[str] = []
    try:
        import tomllib

        data = tomllib.loads(content)
    except Exception:
        return packages

    deps = data.get("project", {}).get("dependencies", [])
    for dep in deps:
        name = re.split(r"[<>=!\[;]", str(dep))[0].strip().lower()
        if name:
            packages.append(name)

    poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
    for name in poetry_deps:
        if name != "python":
            packages.append(name.lower())

    return packages


def _parse_package_json(content: str) -> tuple[list[str], list[str]]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return [], []

    deps = list((data.get("dependencies") or {}).keys())
    dev_deps = list((data.get("devDependencies") or {}).keys())
    return [d.lower() for d in deps], [d.lower() for d in dev_deps]


def analyze_dependencies(ctx: AnalysisContext) -> list[dict]:
    findings: list[dict] = []
    root = ctx.root

    manifest_files = scan_manifest_files(root)

    has_python = any(f.suffix == ".py" for f in ctx.files)
    has_js = any(f.suffix.lower() in {".js", ".jsx", ".ts", ".tsx"} for f in ctx.files)

    if has_python and "requirements.txt" not in manifest_files and "pyproject.toml" not in manifest_files:
        findings.append(
            create_finding(
                type="missing_dependency_file",
                severity="low",
                category="architecture",
                file=".",
                line=0,
                message="Python project missing requirements.txt or pyproject.toml",
                evidence={"issue": "Missing Dependency File", "expected": ["requirements.txt", "pyproject.toml"]},
            )
        )

    if has_js and "package.json" not in manifest_files:
        findings.append(
            create_finding(
                type="missing_dependency_file",
                severity="low",
                category="architecture",
                file=".",
                line=0,
                message="JavaScript/TypeScript project missing package.json",
                evidence={"issue": "Missing Dependency File", "expected": ["package.json"]},
            )
        )

    all_packages: list[str] = []
    package_sources: dict[str, str] = {}

    if "package.json" in manifest_files:
        path = manifest_files["package.json"]
        try:
            deps, dev_deps = _parse_package_json(path.read_text(encoding="utf-8", errors="ignore"))
            rel = path.relative_to(root).as_posix()
            combined = deps + dev_deps
            all_packages.extend(combined)
            for pkg in combined:
                package_sources[pkg] = rel

            if len(deps) >= settings.large_dependency_count_threshold:
                findings.append(
                    create_finding(
                        type="large_dependency_count",
                        severity="medium",
                        category="architecture",
                        file=rel,
                        line=0,
                        message=f"Large dependency count: {len(deps)} production dependencies in package.json",
                        evidence={"count": len(deps), "issue": "Large Dependency Count"},
                    )
                )
        except OSError:
            pass

    if "requirements.txt" in manifest_files:
        path = manifest_files["requirements.txt"]
        try:
            deps = _parse_requirements(path.read_text(encoding="utf-8", errors="ignore"))
            rel = path.relative_to(root).as_posix()
            all_packages.extend(deps)
            for pkg in deps:
                package_sources[pkg] = rel

            if len(deps) >= settings.large_dependency_count_threshold:
                findings.append(
                    create_finding(
                        type="large_dependency_count",
                        severity="medium",
                        category="architecture",
                        file=rel,
                        line=0,
                        message=f"Large dependency count: {len(deps)} packages in requirements.txt",
                        evidence={"count": len(deps), "issue": "Large Dependency Count"},
                    )
                )
        except OSError:
            pass

    if "pyproject.toml" in manifest_files:
        path = manifest_files["pyproject.toml"]
        try:
            deps = _parse_pyproject(path.read_text(encoding="utf-8", errors="ignore"))
            rel = path.relative_to(root).as_posix()
            all_packages.extend(deps)
            for pkg in deps:
                package_sources[pkg] = rel

            if len(deps) >= settings.large_dependency_count_threshold:
                findings.append(
                    create_finding(
                        type="large_dependency_count",
                        severity="medium",
                        category="architecture",
                        file=rel,
                        line=0,
                        message=f"Large dependency count: {len(deps)} packages in pyproject.toml",
                        evidence={"count": len(deps), "issue": "Large Dependency Count"},
                    )
                )
        except OSError:
            pass

    # Dependency concentration: same package in multiple manifests
    if len(manifest_files) >= 2 and all_packages:
        from collections import Counter

        counts = Counter(all_packages)
        for pkg, count in counts.items():
            if count >= 2:
                findings.append(
                    create_finding(
                        type="dependency_concentration",
                        severity="low",
                        category="architecture",
                        file=package_sources.get(pkg, "."),
                        line=0,
                        message=f"Dependency '{pkg}' declared in {count} manifest files",
                        evidence={"package": pkg, "count": count, "issue": "Dependency Concentration"},
                    )
                )

    return findings
