export interface Scores {
  maintainability: number;
  security: number;
  architecture: number;
  dead_code: number;
  architecture_risk: number;
}

export interface DeadCodeSummary {
  unused_imports: number;
  unused_variables: number;
  unused_functions: number;
}

export interface DuplicateLogicSummary {
  duplicate_pairs: number;
  high_confidence_duplicates: number;
  medium_confidence_duplicates: number;
  possible_duplicates: number;
}

export interface ArchitectureSummary {
  god_files: number;
  hotspots: number;
  coupling_issues: number;
  circular_dependencies: number;
}

export interface DependencySummary {
  large_dependency_manifests: number;
  missing_manifests: number;
  concentration_issues: number;
}

export interface Metrics {
  files_scanned: number;
  total_lines: number;
  python_files: number;
  javascript_files: number;
  typescript_files: number;
  findings_count: number;
  findings_by_category: Record<string, number>;
  dead_code_summary: DeadCodeSummary;
  duplicate_logic_summary: DuplicateLogicSummary;
  architecture_summary: ArchitectureSummary;
  dependency_summary: DependencySummary;
}

export interface Finding {
  id: string;
  type: string;
  severity: string;
  category: string;
  file: string;
  line: number;
  message: string;
  confidence?: string;
  evidence?: Record<string, unknown>;
  file_a?: string;
  function_a?: string;
  file_b?: string;
  function_b?: string;
  similarity?: number;
}

export type FindingCategory =
  | "all"
  | "maintainability"
  | "security"
  | "architecture"
  | "dead_code";

export type DuplicateSortKey = "similarity" | "confidence" | "severity";

export interface AnalysisResult {
  repository_name: string;
  metrics: Metrics;
  scores: Scores;
  findings: Finding[];
  ai_report: string;
  prompt_export?: string | null;
}

export type AnalysisState = "idle" | "uploading" | "analyzing" | "complete" | "error";

export const FINDING_CATEGORIES: { value: FindingCategory; label: string }[] = [
  { value: "all", label: "All" },
  { value: "maintainability", label: "Maintainability" },
  { value: "security", label: "Security" },
  { value: "architecture", label: "Architecture" },
  { value: "dead_code", label: "Dead Code" },
];
