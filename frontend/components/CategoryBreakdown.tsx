import type { Metrics } from "@/types/analysis";

interface CategoryBreakdownProps {
  metrics: Metrics;
}

const CATEGORY_LABELS: Record<string, string> = {
  maintainability: "Maintainability",
  security: "Security",
  architecture: "Architecture",
  dead_code: "Dead Code",
};

export default function CategoryBreakdown({ metrics }: CategoryBreakdownProps) {
  const categories = Object.entries(metrics.findings_by_category || {});

  if (categories.length === 0) {
    return null;
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6">
      <h3 className="text-lg font-semibold text-slate-900">Findings by Category</h3>
      <p className="mt-1 text-sm text-slate-500">
        Dead code: {metrics.dead_code_summary?.unused_imports ?? 0} imports,{" "}
        {metrics.dead_code_summary?.unused_variables ?? 0} variables,{" "}
        {metrics.dead_code_summary?.unused_functions ?? 0} functions
      </p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {categories.map(([category, count]) => (
          <div
            key={category}
            className="rounded-lg border border-slate-100 bg-slate-50 px-4 py-3"
          >
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              {CATEGORY_LABELS[category] || category}
            </p>
            <p className="mt-1 text-2xl font-bold text-slate-900">{count}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
