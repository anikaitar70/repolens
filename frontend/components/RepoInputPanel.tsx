"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchUploadLimits, type UploadLimits } from "@/lib/api";
import { formatFileSize, zipFolderFiles } from "@/lib/zipFolder";

type InputMode = "zip" | "folder" | "git";

interface RepoInputPanelProps {
  onUpload: (file: File) => void;
  onFolderPrepare?: (message: string) => void;
  onGitSubmit: (url: string, branch?: string, token?: string) => void;
  onError?: (message: string) => void;
  disabled?: boolean;
}

const MODES: { id: InputMode; label: string; hint: string }[] = [
  {
    id: "zip",
    label: "ZIP file",
    hint: "Upload a pre-made .zip of your repository",
  },
  {
    id: "folder",
    label: "Local folder",
    hint: "We zip it for you and skip node_modules, .git, dist, etc.",
  },
  {
    id: "git",
    label: "Git URL",
    hint: "Analyze a public GitHub, GitLab, or Bitbucket repo",
  },
];

export default function RepoInputPanel({
  onUpload,
  onFolderPrepare,
  onGitSubmit,
  onError,
  disabled,
}: RepoInputPanelProps) {
  const [mode, setMode] = useState<InputMode>("folder");
  const [isDragging, setIsDragging] = useState(false);
  const [limits, setLimits] = useState<UploadLimits | null>(null);
  const [isZipping, setIsZipping] = useState(false);
  const [gitUrl, setGitUrl] = useState("");
  const [gitBranch, setGitBranch] = useState("");
  const [gitToken, setGitToken] = useState("");

  const zipInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchUploadLimits().then(setLimits);
  }, []);

  const reject = useCallback(
    (message: string) => {
      if (onError) onError(message);
      else alert(message);
    },
    [onError],
  );

  const maxBytes = limits?.max_upload_bytes ?? 157_286_400;
  const limitLabel = limits?.max_upload_label ?? "150 MB";

  const validateZipSize = useCallback(
    (file: File) => {
      if (file.size > maxBytes) {
        reject(
          `ZIP is too large (${formatFileSize(file.size)}). Maximum upload size is ${limitLabel}. ` +
            "Try the Local folder option — we automatically exclude node_modules, .git, and build output.",
        );
        return false;
      }
      return true;
    },
    [maxBytes, limitLabel, reject],
  );

  const handleZipFile = useCallback(
    (file: File | undefined) => {
      if (!file || disabled || isZipping) return;
      if (!file.name.toLowerCase().endsWith(".zip")) {
        reject("Please upload a ZIP file.");
        return;
      }
      if (!validateZipSize(file)) return;
      onUpload(file);
    },
    [disabled, isZipping, onUpload, reject, validateZipSize],
  );

  const handleFolderFiles = useCallback(
    async (fileList: FileList | null) => {
      if (!fileList || fileList.length === 0 || disabled || isZipping) return;

      setIsZipping(true);
      try {
        const files = Array.from(fileList);
        const result = await zipFolderFiles(files, (message) => onFolderPrepare?.(message));

        if (!validateZipSize(result.file)) return;

        onFolderPrepare?.(
          `Prepared ${result.includedFiles} files` +
            (result.skippedPaths > 0 ? ` (skipped ${result.skippedPaths} ignored paths)` : "") +
            ` · ${formatFileSize(result.file.size)}`,
        );
        onUpload(result.file);
      } catch (err) {
        reject(err instanceof Error ? err.message : "Failed to prepare folder.");
      } finally {
        setIsZipping(false);
      }
    },
    [disabled, isZipping, onFolderPrepare, onUpload, reject, validateZipSize],
  );

  const handleGitAnalyze = () => {
    if (disabled || isZipping) return;
    const url = gitUrl.trim();
    if (!url) {
      reject("Enter a git repository URL.");
      return;
    }
    onGitSubmit(
      url,
      gitBranch.trim() || undefined,
      gitToken.trim() || undefined,
    );
  };

  const onZipDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleZipFile(e.dataTransfer.files[0]);
  };

  const activeHint = MODES.find((m) => m.id === mode)?.hint ?? "";

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6">
      <div className="mb-5">
        <h3 className="text-lg font-semibold text-slate-900">Add your repository</h3>
        <p className="mt-1 text-sm text-slate-500">
          Choose how to provide your code · max upload {limitLabel}
        </p>
      </div>

      <div className="mb-5 grid gap-2 sm:grid-cols-3">
        {MODES.map((item) => (
          <button
            key={item.id}
            type="button"
            disabled={disabled || isZipping}
            onClick={() => setMode(item.id)}
            className={`rounded-lg border px-3 py-3 text-left text-sm transition-colors ${
              mode === item.id
                ? "border-blue-500 bg-blue-50 text-blue-900"
                : "border-slate-200 bg-white text-slate-700 hover:border-slate-300"
            }`}
          >
            <span className="block font-medium">{item.label}</span>
            <span className="mt-1 block text-xs opacity-80">{item.hint}</span>
          </button>
        ))}
      </div>

      <p className="mb-4 text-xs text-slate-400">{activeHint}</p>

      {mode === "zip" && (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={onZipDrop}
          className={`rounded-xl border-2 border-dashed p-10 text-center transition-colors ${
            isDragging
              ? "border-blue-500 bg-blue-50"
              : "border-slate-300 hover:border-slate-400"
          } ${disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}
          onClick={() => !disabled && zipInputRef.current?.click()}
        >
          <input
            ref={zipInputRef}
            type="file"
            accept=".zip"
            className="hidden"
            disabled={disabled}
            onChange={(e) => handleZipFile(e.target.files?.[0])}
          />
          <p className="font-medium text-slate-900">Drop your ZIP here or click to browse</p>
          <p className="mt-2 text-sm text-slate-500">
            For large repos, try <strong>Local folder</strong> — we exclude heavy folders automatically
          </p>
        </div>
      )}

      {mode === "folder" && (
        <div
          className={`rounded-xl border-2 border-dashed p-10 text-center transition-colors border-slate-300 ${
            disabled || isZipping ? "cursor-not-allowed opacity-60" : "cursor-pointer hover:border-slate-400"
          }`}
          onClick={() => !disabled && !isZipping && folderInputRef.current?.click()}
        >
          <input
            ref={folderInputRef}
            type="file"
            className="hidden"
            disabled={disabled || isZipping}
            // @ts-expect-error webkitdirectory is supported in Chromium-based browsers
            webkitdirectory=""
            directory=""
            multiple
            onChange={(e) => {
              void handleFolderFiles(e.target.files);
              e.target.value = "";
            }}
          />
          <p className="font-medium text-slate-900">
            {isZipping ? "Preparing your folder…" : "Select your project folder"}
          </p>
          <p className="mt-2 text-sm text-slate-500">
            Automatically skips node_modules, .git, dist, build, .next, venv, and other generated folders
          </p>
        </div>
      )}

      {mode === "git" && (
        <div className="space-y-4">
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Repository URL</span>
            <input
              type="url"
              value={gitUrl}
              onChange={(e) => setGitUrl(e.target.value)}
              placeholder="https://github.com/user/repo"
              disabled={disabled}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </label>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block text-sm">
              <span className="mb-1 block font-medium text-slate-700">Branch (optional)</span>
              <input
                type="text"
                value={gitBranch}
                onChange={(e) => setGitBranch(e.target.value)}
                placeholder="main"
                disabled={disabled}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </label>

            <label className="block text-sm">
              <span className="mb-1 block font-medium text-slate-700">Access token (optional)</span>
              <input
                type="password"
                value={gitToken}
                onChange={(e) => setGitToken(e.target.value)}
                placeholder="For private repos only"
                disabled={disabled}
                autoComplete="off"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </label>
          </div>

          <button
            type="button"
            onClick={handleGitAnalyze}
            disabled={disabled}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
          >
            Clone &amp; Analyze
          </button>

          <p className="text-xs text-slate-400">
            Public repos on GitHub, GitLab, and Bitbucket. Token stays in your browser and is sent only for this request.
          </p>
        </div>
      )}
    </div>
  );
}
