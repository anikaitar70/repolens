import ReactMarkdown from "react-markdown";

interface AuditReportProps {
  report: string;
}

export default function AuditReport({ report }: AuditReportProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-6 py-4">
        <h3 className="text-lg font-semibold text-slate-900">AI Audit Report</h3>
        <p className="text-sm text-slate-500">Generated from structured findings</p>
      </div>
      <div className="prose prose-slate max-w-none px-6 py-6">
        <ReactMarkdown>{report}</ReactMarkdown>
      </div>
    </div>
  );
}
