interface SourceRepositoriesProps {
  sources: { source_repo: string; source_commit: string }[];
}

export function SourceRepositories({ sources }: SourceRepositoriesProps) {
  return (
    <section data-testid="pcs-section-source-repos">
      <h2 className="text-lg font-medium">Source Repositories</h2>
      {sources.length === 0 ? (
        <p className="mt-2 text-sm text-gray-600">No source metadata recorded.</p>
      ) : (
        <ul className="mt-3 space-y-2">
          {sources.map((s) => (
            <li
              key={`${s.source_repo}:${s.source_commit}`}
              className="rounded border p-3 text-sm"
            >
              <p data-testid="pcs-source-repo">
                <span className="font-medium">Repository:</span>{" "}
                <a
                  href={s.source_repo}
                  className="text-blue-600 hover:underline break-all"
                  target="_blank"
                  rel="noreferrer"
                >
                  {s.source_repo}
                </a>
              </p>
              <p className="mt-1 font-mono text-xs" data-testid="pcs-source-commit">
                <span className="font-medium font-sans">Commit:</span> {s.source_commit}
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
