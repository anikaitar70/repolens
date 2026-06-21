"use client";

import { useState } from "react";
import { analyzeRepository } from "@/lib/api";
import type { AnalysisResult, AnalysisState } from "@/types/analysis";
import AnalysisProgress from "@/components/AnalysisProgress";
import CategoryBreakdown from "@/components/CategoryBreakdown";
import DuplicateLogicTable from "@/components/DuplicateLogicTable";
import AuditReport from "@/components/AuditReport";
import FindingsTable from "@/components/FindingsTable";
import Hero from "@/components/Hero";
import ScoreCards from "@/components/ScoreCards";
import UploadArea from "@/components/UploadArea";

export default function HomePage() {
  const [state, setState] = useState<AnalysisState>("idle");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async (file: File) => {
    setState("analyzing");
    setError(null);
    setResult(null);

    try {
      const data = await analyzeRepository(file);
      setResult(data);
      setState("complete");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
      setState("error");
    }
  };

  const handleReset = () => {
    setState("idle");
    setResult(null);
    setError(null);
  };

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
          <span className="text-lg font-bold text-slate-900">RepoLens</span>
          {state === "complete" && (
            <button
              onClick={handleReset}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              New Analysis
            </button>
          )}
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
        {state === "idle" && (
          <div className="space-y-10">
            <Hero />
            <UploadArea onUpload={handleUpload} />
          </div>
        )}

        {state === "analyzing" && (
          <div className="space-y-10">
            <Hero />
            <AnalysisProgress />
          </div>
        )}

        {state === "error" && (
          <div className="space-y-6">
            <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center">
              <p className="font-medium text-red-800">{error}</p>
              <button
                onClick={handleReset}
                className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
              >
                Try Again
              </button>
            </div>
          </div>
        )}

        {state === "complete" && result && (
          <div className="space-y-8">
            <ScoreCards
              metrics={result.metrics}
              scores={result.scores}
              repositoryName={result.repository_name}
            />
            <CategoryBreakdown metrics={result.metrics} />
            <DuplicateLogicTable
              findings={result.findings}
              summary={result.metrics.duplicate_logic_summary}
            />
            <FindingsTable findings={result.findings} />
            <AuditReport report={result.ai_report} />
          </div>
        )}
      </div>

      <footer className="mt-16 border-t border-slate-200 bg-white py-6">
        <div className="mx-auto max-w-6xl px-4 text-center text-sm text-slate-500 sm:px-6">
          RepoLens — Analysis first, AI second.
        </div>
      </footer>
    </main>
  );
}
