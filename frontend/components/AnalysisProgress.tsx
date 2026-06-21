interface AnalysisProgressProps {
  message?: string;
}

export default function AnalysisProgress({
  message = "Analyzing repository...",
}: AnalysisProgressProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-8 text-center">
      <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-blue-600" />
      <p className="font-medium text-slate-900">{message}</p>
      <p className="mt-1 text-sm text-slate-500">
        Running analyzers and generating report...
      </p>
    </div>
  );
}
