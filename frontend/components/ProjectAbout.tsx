const TECHNOLOGIES = [
  "Next.js",
  "TypeScript",
  "FastAPI",
  "Python",
  "Tree-sitter",
  "Sentence Transformers",
  "Docker",
  "Tailwind CSS",
] as const;

export default function ProjectAbout() {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6 sm:p-8">
      <p className="text-xs font-semibold uppercase tracking-wide text-blue-600">
        About this project
      </p>
      <h2 className="mt-2 text-xl font-bold text-slate-900 sm:text-2xl">
        AI-assisted repository architecture review
      </h2>
      <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-600 sm:text-base">
        RepoLens runs deterministic static analysis on Python, JavaScript, and TypeScript
        codebases — security patterns, complexity, dead code, circular imports, duplicate
        logic, and architecture risk — then optionally generates an AI audit report with
        your own API key or exports a prompt you can paste into any LLM.
      </p>

      <div className="mt-5">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Technologies
        </p>
        <ul className="mt-2 flex flex-wrap gap-2">
          {TECHNOLOGIES.map((tech) => (
            <li
              key={tech}
              className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-700"
            >
              {tech}
            </li>
          ))}
        </ul>
      </div>

      <p className="mt-5 text-sm text-slate-600">
        Built by{" "}
        <a
          href="https://anikait.page"
          target="_blank"
          rel="noopener noreferrer"
          className="font-medium text-blue-600 underline decoration-blue-200 underline-offset-2 hover:text-blue-700"
        >
          Anikait
        </a>
        {" · "}
        <a
          href="https://anikait.page"
          target="_blank"
          rel="noopener noreferrer"
          className="text-slate-500 hover:text-slate-700"
        >
          anikait.page
        </a>
      </p>
    </section>
  );
}
