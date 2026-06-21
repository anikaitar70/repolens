"use client";

import { useMemo, useState } from "react";
import type { DuplicateSortKey, Finding } from "@/types/analysis";

interface DuplicateLogicTableProps {
  findings: Finding[];
  summary: {
    duplicate_pairs: number;
    high_confidence_duplicates: number;
    medium_confidence_duplicates: number;
    possible_duplicates: number;
  };
}

const CONFIDENCE_ORDER: Record<string, number> = { high: 0, medium: 1, low: 2 };
const SEVERITY_ORDER: Record<string, number> = { high: 0, medium: 1, low: 2 };

function confidenceBadge(confidence?: string) {
  const styles: Record<string, string> = {
    high: "bg-emerald-100 text-emerald-800",
    medium: "bg-amber-100 text-amber-800",
    low: "bg-slate-100 text-slate-700",
  };
  const label = confidence ?? "unknown";
  return (
    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${styles[label] || styles.low}`}>
      {label}
    </span>
  );
}

export default function DuplicateLogicTable({ findings, summary }: DuplicateLogicTableProps) {
  const [sortBy, setSortBy] = useState<DuplicateSortKey>("similarity");

  const duplicates = useMemo(
    () => findings.filter((finding) => finding.type === "duplicate_logic"),
    [findings]
  );

  const sorted = useMemo(() => {
    const items = [...duplicates];
    items.sort((a, b) => {
      if (sortBy === "similarity") {
        return (b.similarity ?? 0) - (a.similarity ?? 0);
      }
      if (sortBy === "confidence") {
        return (
          (CONFIDENCE_ORDER[a.confidence ?? "low"] ?? 3) -
          (CONFIDENCE_ORDER[b.confidence ?? "low"] ?? 3)
        );
      }
      return (
        (SEVERITY_ORDER[a.severity] ?? 3) - (SEVERITY_ORDER[b.severity] ?? 3)
      );
    });
    return items;
  }, [duplicates, sortBy]);

  if (duplicates.length === 0) {
    return null;
  }

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-6 py-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Duplicate Logic</h3>
            <p className="text-sm text-slate-500">
              {summary.duplicate_pairs} pairs detected — high: {summary.high_confidence_duplicates},
              medium: {summary.medium_confidence_duplicates}, possible: {summary.possible_duplicates}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {(["similarity", "confidence", "severity"] as DuplicateSortKey[]).map((key) => (
              <button
                key={key}
                type="button"
                onClick={() => setSortBy(key)}
                className={`rounded-full px-3 py-1 text-xs font-medium capitalize transition-colors ${
                  sortBy === key
                    ? "bg-slate-900 text-white"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                Sort by {key}
              </button>
            ))}
          </div>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50">
            <tr>
              <th className="px-6 py-3 font-medium text-slate-600">Similarity</th>
              <th className="px-6 py-3 font-medium text-slate-600">Confidence</th>
              <th className="px-6 py-3 font-medium text-slate-600">Function A</th>
              <th className="px-6 py-3 font-medium text-slate-600">Function B</th>
              <th className="px-6 py-3 font-medium text-slate-600">Severity</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {sorted.map((finding) => (
              <tr key={finding.id} className="hover:bg-slate-50">
                <td className="px-6 py-4 font-mono text-sm font-semibold text-slate-900">
                  {((finding.similarity ?? finding.evidence?.similarity as number) || 0).toFixed(2)}
                </td>
                <td className="px-6 py-4">{confidenceBadge(finding.confidence)}</td>
                <td className="px-6 py-4 font-mono text-xs text-slate-600">
                  {(finding.function_a as string) || (finding.evidence?.function_a as string)} —{" "}
                  {(finding.file_a as string) || (finding.evidence?.file_a as string)}
                </td>
                <td className="px-6 py-4 font-mono text-xs text-slate-600">
                  {(finding.function_b as string) || (finding.evidence?.function_b as string)} —{" "}
                  {(finding.file_b as string) || (finding.evidence?.file_b as string)}
                </td>
                <td className="px-6 py-4 capitalize text-slate-700">{finding.severity}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
