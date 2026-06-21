export interface Scores {
  maintainability: number;
  security: number;
  architecture: number;
}

export interface Metrics {
  files_scanned: number;
  total_lines: number;
  python_files: number;
  javascript_files: number;
  typescript_files: number;
  findings_count: number;
}

export interface Finding {
  type: string;
  severity: string;
  file?: string;
  function?: string;
  lines?: number;
  complexity?: number;
  issue?: string;
  line?: number;
  chain?: string[];
  description?: string;
}

export interface AnalysisResult {
  repository_name: string;
  metrics: Metrics;
  scores: Scores;
  findings: Finding[];
  ai_report: string;
}

export type AnalysisState = "idle" | "uploading" | "analyzing" | "complete" | "error";
