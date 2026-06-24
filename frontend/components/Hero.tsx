export default function Hero() {
  return (
    <section className="text-center">
      <div className="mb-4 inline-flex items-center rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600">
        Static analysis first · AI report second
      </div>
      <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
        RepoLens
      </h1>
      <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-600">
        AI-Powered Repository Audit
      </p>
      <p className="mx-auto mt-2 max-w-xl text-sm text-slate-500">
        Upload a ZIP, select a local folder, or paste a Git URL. Deterministic analyzers find
        the issues; optional BYOK AI writes the audit report.
      </p>
    </section>
  );
}
