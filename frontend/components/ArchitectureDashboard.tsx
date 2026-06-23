"use client";

import type { ArchitectureSummary, DependencySummary, Finding } from "@/types/analysis";

interface ArchitectureDashboardProps {
  findings: Finding[];
  architectureSummary: ArchitectureSummary;
  dependencySummary: DependencySummary;
  architectureRisk: number;
}

function SummaryCard({ label, value, tone }: { label: string; value: number; tone?: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <p className="text-sm text-slate-500">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${tone ?? "text-slate-900"}`}>{value}</p>
    </div>
  );
}

export default function ArchitectureDashboard({
  findings,
  architectureSummary,
  dependencySummary,
  architectureRisk,
}: ArchitectureDashboardProps) {
  const hotspots = findings.filter((f) => f.type === "architectural_hotspot");
  const godFiles = findings.filter((f) => f.type === "god_file");
  const coupling = findings.filter((f) => f.type === "high_coupling");
  const cycles = findings.filter((f) => f.type === "circular_dependency");

  const riskTone =
    architectureRisk >= 80
      ? "text-emerald-600"
      : architectureRisk >= 60
        ? "text-amber-600"
        : "text-red-600";

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-slate-900">Architecture Overview</h3>
        <p className="text-sm text-slate-500">
          Dependency graph intelligence, coupling analysis, and architectural hotspots.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <SummaryCard label="Architecture Risk" value={architectureRisk} tone={riskTone} />
        <SummaryCard label="God Files" value={architectureSummary.god_files} />
        <SummaryCard label="Hotspots" value={architectureSummary.hotspots} />
        <SummaryCard label="Coupling Issues" value={architectureSummary.coupling_issues} />
        <SummaryCard label="Circular Deps" value={architectureSummary.circular_dependencies} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Section title="Architectural Hotspots" items={hotspots} empty="No hotspots detected." />
        <Section title="God Files" items={godFiles} empty="No god files detected." />
        <Section title="Coupling Issues" items={coupling} empty="No coupling issues detected." />
        <Section title="Circular Dependencies" items={cycles} empty="No circular dependencies detected." />
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <h4 className="font-medium text-slate-900">Dependency Intelligence</h4>
        <div className="mt-3 grid gap-3 sm:grid-cols-3">
          <SummaryCard
            label="Large Manifests"
            value={dependencySummary.large_dependency_manifests}
          />
          <SummaryCard label="Missing Manifests" value={dependencySummary.missing_manifests} />
          <SummaryCard
            label="Concentration Issues"
            value={dependencySummary.concentration_issues}
          />
        </div>
      </div>
    </div>
  );
}

function Section({
  title,
  items,
  empty,
}: {
  title: string;
  items: Finding[];
  empty: string;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <h4 className="font-medium text-slate-900">{title}</h4>
      {items.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">{empty}</p>
      ) : (
        <ul className="mt-3 space-y-2 text-sm text-slate-700">
          {items.slice(0, 8).map((item) => (
            <li key={item.id} className="rounded-lg bg-slate-50 px-3 py-2">
              <span className="font-mono text-xs text-slate-500">{item.file}</span>
              <p>{item.message}</p>
              {Array.isArray(item.evidence?.chain) && (
                <p className="mt-1 text-xs text-slate-500">
                  {(item.evidence.chain as string[]).join(" → ")}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
