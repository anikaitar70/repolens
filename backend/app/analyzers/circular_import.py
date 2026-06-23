from app.analysis_context import AnalysisContext
from app.findings import create_finding
from app.services.dependency_graph import (
    build_dependency_graphs,
    find_cycles,
    module_to_display_path,
)


def detect_circular_imports(ctx: AnalysisContext) -> list[dict]:
    findings: list[dict] = []
    root = ctx.root

    for graph in build_dependency_graphs(root, ctx.files):
        is_python = graph.language == "python"
        for cycle in find_cycles(graph):
            chain = [module_to_display_path(module, is_python) for module in cycle]
            chain_str = " -> ".join(cycle[:-1] + [cycle[0]])
            findings.append(
                create_finding(
                    type="circular_dependency",
                    severity="high",
                    category="architecture",
                    file=chain[0] if chain else "",
                    line=0,
                    message=f"Circular dependency detected: {chain_str}",
                    evidence={"issue": "Circular Dependency", "chain": chain},
                )
            )

    return findings
