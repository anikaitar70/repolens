/** Directory names skipped when zipping a local folder (mirrors backend scanner.py). */

export const IGNORED_DIRS = new Set([
  "node_modules",
  ".git",
  "dist",
  "build",
  ".next",
  "coverage",
  "venv",
  ".venv",
  "env",
  "__pycache__",
  ".turbo",
  ".cache",
  "target",
  "vendor",
]);

export function shouldIgnorePath(relativePath: string): boolean {
  const parts = relativePath.replace(/\\/g, "/").split("/").filter(Boolean);
  return parts.some((part) => IGNORED_DIRS.has(part) || part.startsWith("."));
}
