import type { AnalysisResult } from "@/types/analysis";
import { normalizeAnalysisResult } from "@/lib/normalize";
import type { AiSettings } from "@/lib/aiSettings";
import { hasAiKey } from "@/lib/aiSettings";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8080";

export interface UploadLimits {
  max_upload_bytes: number;
  max_upload_label: string;
  max_extracted_bytes: number;
  max_extracted_label: string;
  max_extracted_files: number;
  max_single_file_bytes: number;
  max_single_file_label: string;
}

const DEFAULT_LIMITS: UploadLimits = {
  max_upload_bytes: 104_857_600,
  max_upload_label: "100 MB",
  max_extracted_bytes: 262_144_000,
  max_extracted_label: "250 MB",
  max_extracted_files: 5000,
  max_single_file_bytes: 20_971_520,
  max_single_file_label: "20 MB",
};

function parseErrorDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => String(item)).join(", ");
  }
  return "Analysis failed";
}

async function parseApiError(response: Response, fallback: string): Promise<string> {
  if (response.status === 413) {
    const error = await response.json().catch(() => null);
    if (error?.detail && typeof error.detail === "string") {
      return error.detail;
    }
    return (
      "File or repository is too large. Maximum ZIP size is 100 MB. " +
      "Exclude node_modules, .git, and build folders before zipping."
    );
  }

  const error = await response.json().catch(() => ({ detail: fallback }));
  return parseErrorDetail(error.detail);
}

function aiHeaders(settings?: AiSettings): HeadersInit {
  if (!settings || !hasAiKey(settings)) {
    return {};
  }
  return {
    "X-AI-Provider": settings.provider,
    "X-AI-Model": settings.model,
    "X-AI-Api-Key": settings.apiKey,
  };
}

export async function fetchUploadLimits(): Promise<UploadLimits> {
  try {
    const response = await fetch(`${API_URL}/api/limits`);
    if (!response.ok) return DEFAULT_LIMITS;
    return { ...DEFAULT_LIMITS, ...(await response.json()) };
  } catch {
    return DEFAULT_LIMITS;
  }
}

export async function analyzeRepository(
  file: File,
  aiSettings?: AiSettings,
): Promise<AnalysisResult> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_URL}/api/analyze`, {
    method: "POST",
    body: formData,
    headers: aiHeaders(aiSettings),
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, "Analysis failed"));
  }

  return normalizeAnalysisResult(await response.json());
}

export async function testAiConnection(
  settings: AiSettings,
): Promise<{ status: string; message: string }> {
  const response = await fetch(`${API_URL}/api/ai/test`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      provider: settings.provider,
      model: settings.model,
      api_key: settings.apiKey,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Connection test failed" }));
    throw new Error(parseErrorDetail(error.detail));
  }

  return response.json();
}
