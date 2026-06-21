import type { AnalysisResult, Finding, Metrics, Scores } from "@/types/analysis";

type RawFinding = Partial<Finding> & {
  description?: string;
  issue?: string;
  function?: string;
  lines?: number;
  complexity?: number;
  chain?: string[];
};

function inferCategory(type: string): Finding["category"] {
  switch (type) {
    case "security":
      return "security";
    case "circular_dependency":
    case "architecture":
      return "architecture";
    case "unused_import":
    case "unused_variable":
    case "unused_function":
      return "dead_code";
    default:
      return "maintainability";
  }
}

function buildMessage(raw: RawFinding): string {
  if (raw.message) return raw.message;
  if (raw.description) return raw.description;
  if (raw.issue) return raw.issue;
  if (raw.type === "large_file" && raw.lines) {
    return `File has ${raw.lines} lines`;
  }
  if (raw.type === "large_function" && raw.function) {
    return `Function '${raw.function}' has ${raw.lines ?? "?"} lines`;
  }
  if (raw.type === "complexity" && raw.function) {
    return `Function '${raw.function}' complexity: ${raw.complexity ?? "?"}`;
  }
  if (raw.chain?.length) {
    return raw.chain.join(" → ");
  }
  return "Analysis finding";
}

export function normalizeFinding(raw: RawFinding, index: number): Finding {
  const type = raw.type ?? "unknown";
  const category = (raw.category as Finding["category"]) || inferCategory(type);

  return {
    id: raw.id ?? `finding-${index}`,
    type,
    severity: raw.severity ?? "low",
    category,
    file: raw.file ?? (raw.chain ? raw.chain.join(", ") : "—"),
    line: raw.line ?? 0,
    message: buildMessage(raw),
    confidence: raw.confidence,
    evidence: raw.evidence ?? {
      ...(raw.function ? { function: raw.function } : {}),
      ...(raw.lines ? { lines: raw.lines } : {}),
      ...(raw.complexity ? { complexity: raw.complexity } : {}),
      ...(raw.issue ? { issue: raw.issue } : {}),
      ...(raw.chain ? { chain: raw.chain } : {}),
    },
  };
}

export function normalizeAnalysisResult(data: AnalysisResult): AnalysisResult {
  const findings = (data.findings ?? []).map(normalizeFinding);

  const scores: Scores = {
    maintainability: data.scores?.maintainability ?? 100,
    security: data.scores?.security ?? 100,
    architecture: data.scores?.architecture ?? 100,
    dead_code: data.scores?.dead_code ?? 100,
  };

  const metrics: Metrics = {
    files_scanned: data.metrics?.files_scanned ?? 0,
    total_lines: data.metrics?.total_lines ?? 0,
    python_files: data.metrics?.python_files ?? 0,
    javascript_files: data.metrics?.javascript_files ?? 0,
    typescript_files: data.metrics?.typescript_files ?? 0,
    findings_count: data.metrics?.findings_count ?? findings.length,
    findings_by_category: data.metrics?.findings_by_category ?? {},
    dead_code_summary: data.metrics?.dead_code_summary ?? {
      unused_imports: 0,
      unused_variables: 0,
      unused_functions: 0,
    },
  };

  if (Object.keys(metrics.findings_by_category).length === 0 && findings.length > 0) {
    metrics.findings_by_category = findings.reduce<Record<string, number>>((acc, finding) => {
      acc[finding.category] = (acc[finding.category] ?? 0) + 1;
      return acc;
    }, {});
  }

  return {
    ...data,
    findings,
    scores,
    metrics,
  };
}
