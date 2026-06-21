export interface Scores {
  maintainability: number;
  security: number;
  architecture: number;
  dead_code: number;
}

export interface DeadCodeSummary {
  unused_imports: number;
  unused_variables: number;
  unused_functions: number;
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
}

export type FindingCategory =
  | "all"
  | "maintainability"
  | "security"
  | "architecture"
  | "dead_code";

export interface AnalysisResult {
  repository_name: string;
  metrics: Metrics;
  scores: Scores;
  findings: Finding[];
  ai_report: string;
}

export type AnalysisState = "idle" | "uploading" | "analyzing" | "complete" | "error";

export const FINDING_CATEGORIES: { value: FindingCategory; label: string }[] = [
  { value: "all", label: "All" },
  { value: "maintainability", label: "Maintainability" },
  { value: "security", label: "Security" },
  { value: "architecture", label: "Architecture" },
  { value: "dead_code", label: "Dead Code" },
];
