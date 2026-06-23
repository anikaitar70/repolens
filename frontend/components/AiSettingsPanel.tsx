"use client";

import { useEffect, useState } from "react";
import {
  DEFAULT_MODELS,
  PROVIDER_LABELS,
  type AiProvider,
  type AiSettings,
  hasAiKey,
  loadAiSettings,
  saveAiSettings,
} from "@/lib/aiSettings";
import { testAiConnection } from "@/lib/api";

type ConnectionStatus = "idle" | "testing" | "connected" | "invalid" | "error";

interface AiSettingsPanelProps {
  onChange?: (settings: AiSettings) => void;
}

export default function AiSettingsPanel({ onChange }: AiSettingsPanelProps) {
  const [settings, setSettings] = useState<AiSettings>(() => loadAiSettings());
  const [status, setStatus] = useState<ConnectionStatus>("idle");
  const [statusMessage, setStatusMessage] = useState("");

  useEffect(() => {
    onChange?.(settings);
  }, [settings, onChange]);

  const update = (partial: Partial<AiSettings>) => {
    const next = { ...settings, ...partial };
    if (partial.provider && partial.provider !== settings.provider) {
      next.model = DEFAULT_MODELS[partial.provider];
    }
    setSettings(next);
    saveAiSettings(next);
    setStatus("idle");
    setStatusMessage("");
  };

  const handleTest = async () => {
    if (!hasAiKey(settings)) {
      setStatus("invalid");
      setStatusMessage("Enter an API key to test.");
      return;
    }

    setStatus("testing");
    setStatusMessage("Testing connection...");
    try {
      const result = await testAiConnection(settings);
      setStatus(result.status as ConnectionStatus);
      setStatusMessage(result.message);
    } catch {
      setStatus("error");
      setStatusMessage("Connection test failed.");
    }
  };

  const statusStyles: Record<ConnectionStatus, string> = {
    idle: "text-slate-500",
    testing: "text-blue-600",
    connected: "text-emerald-600",
    invalid: "text-amber-600",
    error: "text-red-600",
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-slate-900">AI Settings</h3>
        <p className="text-sm text-slate-500">
          API keys are stored in your browser only and sent per request. Never saved on the server.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-700">Provider</span>
          <select
            value={settings.provider}
            onChange={(e) => update({ provider: e.target.value as AiProvider })}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          >
            {(Object.keys(PROVIDER_LABELS) as AiProvider[]).map((provider) => (
              <option key={provider} value={provider}>
                {PROVIDER_LABELS[provider]}
              </option>
            ))}
          </select>
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-700">Model</span>
          <input
            type="text"
            value={settings.model}
            onChange={(e) => update({ model: e.target.value })}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            placeholder={DEFAULT_MODELS[settings.provider]}
          />
        </label>

        <label className="block text-sm sm:col-span-2">
          <span className="mb-1 block font-medium text-slate-700">API Key</span>
          <input
            type="password"
            value={settings.apiKey}
            onChange={(e) => update({ apiKey: e.target.value })}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            placeholder="Paste your API key"
            autoComplete="off"
          />
        </label>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={handleTest}
          disabled={status === "testing"}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
        >
          {status === "testing" ? "Testing..." : "Test Connection"}
        </button>
        {statusMessage && (
          <span className={`text-sm font-medium ${statusStyles[status]}`}>{statusMessage}</span>
        )}
      </div>

      {!hasAiKey(settings) && (
        <p className="mt-3 text-sm text-slate-500">
          No API key configured — analysis will return an AI-ready prompt you can paste into ChatGPT,
          Claude, Gemini, or Grok.
        </p>
      )}
    </div>
  );
}
