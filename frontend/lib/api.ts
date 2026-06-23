import type { AnalysisResult } from "@/types/analysis";
import { normalizeAnalysisResult } from "@/lib/normalize";
import type { AiSettings } from "@/lib/aiSettings";
import { hasAiKey } from "@/lib/aiSettings";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8080";

function parseErrorDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => String(item)).join(", ");
  }
  return "Analysis failed";
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
    const error = await response.json().catch(() => ({ detail: "Analysis failed" }));
    throw new Error(parseErrorDetail(error.detail));
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
