import type { Metrics, Scores } from "@/types/analysis";

interface ScoreCardsProps {
  metrics: Metrics;
  scores: Scores;
  repositoryName: string;
}

function ScoreRing({ label, score }: { label: string; score: number }) {
  const color =
    score >= 80 ? "text-emerald-600" : score >= 60 ? "text-amber-600" : "text-red-600";

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6">
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <p className={`mt-2 text-3xl font-bold ${color}`}>{score}</p>
      <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className={`h-full rounded-full ${
            score >= 80 ? "bg-emerald-500" : score >= 60 ? "bg-amber-500" : "bg-red-500"
          }`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}

export default function ScoreCards({ metrics, scores, repositoryName }: ScoreCardsProps) {
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-slate-900">{repositoryName}</h2>
        <p className="text-sm text-slate-500">Analysis complete</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <div className="rounded-xl border border-slate-200 bg-white p-6">
          <p className="text-sm font-medium text-slate-500">Files Scanned</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">{metrics.files_scanned}</p>
          <p className="mt-1 text-xs text-slate-400">{metrics.total_lines.toLocaleString()} lines</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6">
          <p className="text-sm font-medium text-slate-500">Total Findings</p>
          <p className="mt-2 text-3xl font-bold text-slate-900">{metrics.findings_count}</p>
        </div>

        <ScoreRing label="Maintainability" score={scores.maintainability} />
        <ScoreRing label="Security" score={scores.security} />
        <ScoreRing label="Architecture" score={scores.architecture} />
        <ScoreRing label="Dead Code" score={scores.dead_code ?? 100} />
      </div>
    </div>
  );
}
