"use client";

import { useMemo, useState } from "react";
import type { Finding, FindingCategory } from "@/types/analysis";
import { FINDING_CATEGORIES } from "@/types/analysis";

interface FindingsTableProps {
  findings: Finding[];
}

function severityBadge(severity: string) {
  const styles: Record<string, string> = {
    high: "bg-red-100 text-red-700",
    medium: "bg-amber-100 text-amber-700",
    low: "bg-slate-100 text-slate-700",
  };
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${
        styles[severity] || styles.low
      }`}
    >
      {severity}
    </span>
  );
}

function categoryBadge(category?: string) {
  const value = category ?? "unknown";
  const styles: Record<string, string> = {
    maintainability: "bg-blue-100 text-blue-700",
    security: "bg-red-100 text-red-700",
    architecture: "bg-purple-100 text-purple-700",
    dead_code: "bg-slate-200 text-slate-700",
    unknown: "bg-slate-100 text-slate-700",
  };
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${
        styles[value] || styles.unknown
      }`}
    >
      {value.replace(/_/g, " ")}
    </span>
  );
}

export default function FindingsTable({ findings }: FindingsTableProps) {
  const [category, setCategory] = useState<FindingCategory>("all");

  const filtered = useMemo(() => {
    if (category === "all") return findings;
    return findings.filter((finding) => finding.category === category);
  }, [findings, category]);

  if (findings.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 text-center">
        <p className="text-slate-600">No issues found. Great work!</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-6 py-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Findings</h3>
            <p className="text-sm text-slate-500">
              Showing {filtered.length} of {findings.length} issues
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {FINDING_CATEGORIES.map((item) => (
              <button
                key={item.value}
                type="button"
                onClick={() => setCategory(item.value)}
                className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                  category === item.value
                    ? "bg-slate-900 text-white"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50">
            <tr>
              <th className="px-6 py-3 font-medium text-slate-600">Severity</th>
              <th className="px-6 py-3 font-medium text-slate-600">Category</th>
              <th className="px-6 py-3 font-medium text-slate-600">Type</th>
              <th className="px-6 py-3 font-medium text-slate-600">File</th>
              <th className="px-6 py-3 font-medium text-slate-600">Description</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filtered.map((finding, index) => (
              <tr key={finding.id ?? `${finding.type}-${index}`} className="hover:bg-slate-50">
                <td className="px-6 py-4">{severityBadge(finding.severity)}</td>
                <td className="px-6 py-4">{categoryBadge(finding.category)}</td>
                <td className="px-6 py-4 font-mono text-xs text-slate-700">
                  {finding.type}
                </td>
                <td className="px-6 py-4 font-mono text-xs text-slate-600">
                  {finding.file}
                  {finding.line ? `:${finding.line}` : ""}
                </td>
                <td className="px-6 py-4 text-slate-700">
                  {finding.message}
                  {finding.confidence ? (
                    <span className="ml-2 text-xs text-slate-400">
                      ({finding.confidence} confidence)
                    </span>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
