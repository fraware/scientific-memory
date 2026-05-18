import type { PcsLineageView } from "@/lib/pcsTypes";

interface Props {
  lineage: PcsLineageView;
}

export function LineageView({ lineage }: Props) {
  const commits = lineage.source_commits ?? {};
  const newer = lineage.newer_release_ids ?? [];
  const changed = lineage.changed_artifacts ?? [];
  const hashDiffs = lineage.changed_hashes ?? [];

  return (
    <section data-testid="pcs-section-lineage">
      <h2 className="text-xl font-semibold">Lineage</h2>
      <p className="mt-1 text-sm text-gray-600">
        Proof-carrying release identity for this claim and how it relates to other releases.
      </p>

      {lineage.claim_state ? (
        <p className="mt-3 text-sm">
          Claim state:{" "}
          <span className="rounded bg-gray-100 px-2 py-0.5 font-medium uppercase tracking-wide text-gray-800">
            {lineage.claim_state}
          </span>
        </p>
      ) : null}

      <dl className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
        <dt className="text-gray-500">Current claim</dt>
        <dd>{lineage.claim_id || "—"}</dd>
        <dt className="text-gray-500">Previous release</dt>
        <dd>{lineage.previous_release_id || "—"}</dd>
        <dt className="text-gray-500">Newer release(s)</dt>
        <dd>{newer.length ? newer.join(", ") : "—"}</dd>
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

      {lineage.recommended_action ? (
        <p className="mt-4 rounded border border-blue-100 bg-blue-50 p-3 text-sm text-blue-900">
          <span className="font-medium">Recommended action:</span> {lineage.recommended_action}
        </p>
      ) : null}

      {changed.length > 0 ? (
        <div className="mt-4">
          <h3 className="text-sm font-medium text-gray-700">Changed artifacts</h3>
          <ul className="mt-2 list-inside list-disc text-sm text-gray-700">
            {changed.map((name) => (
              <li key={name}>{name}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {hashDiffs.length > 0 ? (
        <div className="mt-4 overflow-x-auto">
          <h3 className="text-sm font-medium text-gray-700">Changed hashes</h3>
          <table className="mt-2 min-w-full text-left text-xs">
            <thead>
              <tr className="border-b text-gray-500">
                <th className="py-1 pr-4">Artifact</th>
                <th className="py-1 pr-4">Previous</th>
                <th className="py-1">Current</th>
              </tr>
            </thead>
            <tbody>
              {hashDiffs.map((row) => (
                <tr key={row.artifact} className="border-b border-gray-100">
                  <td className="py-1 pr-4 font-mono">{row.artifact}</td>
                  <td className="py-1 pr-4 font-mono break-all">{row.previous || "—"}</td>
                  <td className="py-1 font-mono break-all">{row.current || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

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
