import type { Finding } from "@/types/analysis";

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

function getDescription(finding: Finding): string {
  if (finding.description) return finding.description;
  if (finding.issue) return finding.issue;
  if (finding.type === "large_file") {
    return `File has ${finding.lines} lines`;
  }
  if (finding.type === "large_function") {
    return `Function '${finding.function}' has ${finding.lines} lines`;
  }
  if (finding.type === "complexity") {
    return `Function '${finding.function}' complexity: ${finding.complexity}`;
  }
  if (finding.type === "architecture" && finding.chain) {
    return finding.chain.join(" → ");
  }
  return "—";
}

function getFile(finding: Finding): string {
  if (finding.file) return finding.file;
  if (finding.chain) return finding.chain.join(", ");
  return "—";
}

export default function FindingsTable({ findings }: FindingsTableProps) {
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
        <h3 className="text-lg font-semibold text-slate-900">Findings</h3>
        <p className="text-sm text-slate-500">{findings.length} issues detected</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50">
            <tr>
              <th className="px-6 py-3 font-medium text-slate-600">Severity</th>
              <th className="px-6 py-3 font-medium text-slate-600">Type</th>
              <th className="px-6 py-3 font-medium text-slate-600">File</th>
              <th className="px-6 py-3 font-medium text-slate-600">Description</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {findings.map((finding, index) => (
              <tr key={index} className="hover:bg-slate-50">
                <td className="px-6 py-4">{severityBadge(finding.severity)}</td>
                <td className="px-6 py-4 font-mono text-xs text-slate-700">
                  {finding.type}
                </td>
                <td className="px-6 py-4 font-mono text-xs text-slate-600">
                  {getFile(finding)}
                </td>
                <td className="px-6 py-4 text-slate-700">{getDescription(finding)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
