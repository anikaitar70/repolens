import JSZip from "jszip";
import { shouldIgnorePath } from "@/lib/ignorePaths";

export interface ZipFolderResult {
  file: File;
  includedFiles: number;
  skippedPaths: number;
}

function deriveRepoName(files: File[]): string {
  for (const file of files) {
    const relative = file.webkitRelativePath || file.name;
    const top = relative.replace(/\\/g, "/").split("/")[0];
    if (top) return top;
  }
  return "repository";
}

export async function zipFolderFiles(
  files: File[],
  onProgress?: (message: string) => void,
): Promise<ZipFolderResult> {
  if (files.length === 0) {
    throw new Error("No files selected.");
  }

  const zip = new JSZip();
  const repoName = deriveRepoName(files);
  let includedFiles = 0;
  let skippedPaths = 0;

  onProgress?.("Filtering unnecessary folders (node_modules, .git, dist…)…");

  for (const file of files) {
    const relativePath = (file.webkitRelativePath || file.name).replace(/\\/g, "/");
    if (shouldIgnorePath(relativePath)) {
      skippedPaths += 1;
      continue;
    }

    const zipPath = relativePath.startsWith(`${repoName}/`)
      ? relativePath
      : `${repoName}/${relativePath}`;

    zip.file(zipPath, file);
    includedFiles += 1;

    if (includedFiles % 200 === 0) {
      onProgress?.(`Packaging files… (${includedFiles} included)`);
    }
  }

  if (includedFiles === 0) {
    throw new Error(
      "No files left after filtering. The folder may only contain ignored directories like node_modules or .git.",
    );
  }

  onProgress?.("Creating ZIP archive…");

  const blob = await zip.generateAsync({
    type: "blob",
    compression: "DEFLATE",
    compressionOptions: { level: 6 },
  });

  return {
    file: new File([blob], `${repoName}.zip`, { type: "application/zip" }),
    includedFiles,
    skippedPaths,
  };
}

export function formatFileSize(bytes: number): string {
  if (bytes >= 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
  if (bytes >= 1024) {
    return `${(bytes / 1024).toFixed(0)} KB`;
  }
  return `${bytes} bytes`;
}
