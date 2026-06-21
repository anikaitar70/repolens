"use client";

import { useCallback, useRef, useState } from "react";

interface UploadAreaProps {
  onUpload: (file: File) => void;
  disabled?: boolean;
}

export default function UploadArea({ onUpload, disabled }: UploadAreaProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (file: File | undefined) => {
      if (!file || disabled) return;
      if (!file.name.toLowerCase().endsWith(".zip")) {
        alert("Please upload a ZIP file.");
        return;
      }
      onUpload(file);
    },
    [onUpload, disabled]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      handleFile(e.dataTransfer.files[0]);
    },
    [handleFile]
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={onDrop}
      className={`rounded-xl border-2 border-dashed p-12 text-center transition-colors ${
        isDragging
          ? "border-blue-500 bg-blue-50"
          : "border-slate-300 bg-white hover:border-slate-400"
      } ${disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}
      onClick={() => !disabled && inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".zip"
        className="hidden"
        disabled={disabled}
        onChange={(e) => handleFile(e.target.files?.[0])}
      />
      <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-slate-100">
        <svg
          className="h-6 w-6 text-slate-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
      </div>
      <p className="text-base font-medium text-slate-900">
        Drop your repository ZIP here
      </p>
      <p className="mt-1 text-sm text-slate-500">or click to browse</p>
      <p className="mt-3 text-xs text-slate-400">
        Supports Python, JavaScript, and TypeScript
      </p>
    </div>
  );
}
