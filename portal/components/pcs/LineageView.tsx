import type { PcsLineageView } from "@/lib/pcsTypes";

interface Props {
  lineage: PcsLineageView;
}

export function LineageView({ lineage }: Props) {
  const commits = lineage.source_commits ?? {};
  return (
    <section data-testid="pcs-section-lineage">
      <h2 className="text-xl font-semibold">Lineage</h2>
      <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
        <dt className="text-gray-500">Claim ID</dt>
        <dd>{lineage.claim_id || "—"}</dd>
        <dt className="text-gray-500">Bundle ID</dt>
        <dd>{lineage.bundle_id || "—"}</dd>
        <dt className="text-gray-500">Certificate ID</dt>
        <dd className="font-mono text-xs">{lineage.certificate_id || "—"}</dd>
        <dt className="text-gray-500">Trace hash</dt>
        <dd className="font-mono text-xs break-all">{lineage.trace_hash || "—"}</dd>
        <dt className="text-gray-500">Signed bundle hash</dt>
        <dd className="font-mono text-xs break-all">{lineage.signed_bundle_hash || "—"}</dd>
        <dt className="text-gray-500">Release ID</dt>
        <dd>{lineage.release_id || "—"}</dd>
        <dt className="text-gray-500">Release manifest hash</dt>
        <dd className="font-mono text-xs break-all">{lineage.release_manifest_hash || "—"}</dd>
      </dl>
      {Object.keys(commits).length > 0 ? (
        <div className="mt-4">
          <h3 className="text-sm font-medium text-gray-700">Source commits</h3>
          <ul className="mt-2 space-y-1 font-mono text-xs">
            {Object.entries(commits).map(([repo, commit]) => (
              <li key={repo}>
                <span className="text-gray-500">{repo}:</span> {commit}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
