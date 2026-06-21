import type { AnalysisResult } from "@/types/analysis";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8080";

function parseErrorDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => String(item)).join(", ");
  }
  return "Analysis failed";
}

export async function analyzeRepository(file: File): Promise<AnalysisResult> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_URL}/api/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Analysis failed" }));
    throw new Error(parseErrorDetail(error.detail));
  }

  return response.json();
}
