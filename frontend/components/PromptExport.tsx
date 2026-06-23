"use client";

import { useState } from "react";

interface PromptExportProps {
  prompt: string;
}

export default function PromptExport({ prompt }: PromptExportProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(prompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
      <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">AI-Ready Prompt</h3>
          <p className="text-sm text-slate-500">
            Copy this prompt into ChatGPT, Claude, Gemini, or Grok to generate your audit report.
          </p>
        </div>
        <button
          type="button"
          onClick={handleCopy}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
        >
          {copied ? "Copied!" : "Copy Prompt"}
        </button>
      </div>
      <pre className="max-h-96 overflow-auto whitespace-pre-wrap bg-slate-50 p-6 text-xs text-slate-700">
        {prompt}
      </pre>
    </div>
  );
}
