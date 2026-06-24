"use client";

import { useCallback, useEffect, useState } from "react";
import { analyzeGitRepository, analyzeRepository } from "@/lib/api";
import { DEFAULT_AI_SETTINGS, loadAiSettings, type AiSettings } from "@/lib/aiSettings";
import type { AnalysisResult, AnalysisState } from "@/types/analysis";
import AiSettingsPanel from "@/components/AiSettingsPanel";
import AnalysisProgress from "@/components/AnalysisProgress";
import ArchitectureDashboard from "@/components/ArchitectureDashboard";
import AuditReport from "@/components/AuditReport";
import CategoryBreakdown from "@/components/CategoryBreakdown";
import DuplicateLogicTable from "@/components/DuplicateLogicTable";
import FindingsTable from "@/components/FindingsTable";
import ProjectAbout from "@/components/ProjectAbout";
import Hero from "@/components/Hero";
import PromptExport from "@/components/PromptExport";
import ScoreCards from "@/components/ScoreCards";
import RepoInputPanel from "@/components/RepoInputPanel";

export default function HomePage() {
  const [state, setState] = useState<AnalysisState>("idle");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [aiSettings, setAiSettings] = useState<AiSettings>(DEFAULT_AI_SETTINGS);

  const [progressMessage, setProgressMessage] = useState("Analyzing repository...");

  useEffect(() => {
    setAiSettings(loadAiSettings());
  }, []);

  const handleSettingsChange = useCallback((settings: AiSettings) => {
    setAiSettings(settings);
  }, []);

  const runAnalysis = async (task: () => Promise<AnalysisResult>) => {
    setState("analyzing");
    setError(null);
    setResult(null);

    try {
      const data = await task();
      setResult(data);
      setState("complete");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
      setState("error");
    }
  };

  const handleUpload = async (file: File) => {
    setProgressMessage("Analyzing repository...");
    await runAnalysis(() => analyzeRepository(file, aiSettings));
  };

  const handleGitSubmit = async (url: string, branch?: string, token?: string) => {
    setProgressMessage("Cloning repository...");
    await runAnalysis(() => analyzeGitRepository(url, branch, token, aiSettings));
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
            <ProjectAbout />
            <Hero />
            <AiSettingsPanel onChange={handleSettingsChange} />
            <RepoInputPanel
              onUpload={handleUpload}
              onFolderPrepare={setProgressMessage}
              onGitSubmit={handleGitSubmit}
              onError={(message) => {
                setError(message);
                setState("error");
              }}
            />
          </div>
        )}

        {state === "analyzing" && (
          <div className="space-y-10">
            <Hero />
            <AnalysisProgress message={progressMessage} />
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
            <ArchitectureDashboard
              findings={result.findings}
              architectureSummary={result.metrics.architecture_summary}
              dependencySummary={result.metrics.dependency_summary}
              architectureRisk={result.scores.architecture_risk}
            />
            <CategoryBreakdown metrics={result.metrics} />
            <DuplicateLogicTable
              findings={result.findings}
              summary={result.metrics.duplicate_logic_summary}
            />
            <FindingsTable findings={result.findings} />
            {result.ai_report ? (
              <AuditReport report={result.ai_report} />
            ) : result.prompt_export ? (
              <PromptExport prompt={result.prompt_export} />
            ) : null}
          </div>
        )}
      </div>

      <footer className="mt-16 border-t border-slate-200 bg-white py-6">
        <div className="mx-auto max-w-6xl px-4 text-center text-sm text-slate-500 sm:px-6">
          RepoLens — Analysis first, AI second.{" "}
          <a
            href="https://anikait.page"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-700"
          >
            Built by Anikait
          </a>
        </div>
      </footer>
    </main>
  );
}
