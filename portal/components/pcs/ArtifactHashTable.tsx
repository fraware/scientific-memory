import type { PcsCanonicalDigests, PcsHashRow } from "@/lib/pcsTypes";

const CANONICAL_LABELS: { key: keyof PcsCanonicalDigests; label: string }[] = [
  { key: "claim_artifact", label: "Claim artifact digest" },
  { key: "runtime_receipt", label: "Runtime receipt digest" },
  { key: "trace_certificate", label: "Trace certificate digest" },
  { key: "evidence_bundle", label: "Evidence bundle digest" },
  { key: "signed_bundle", label: "Signed bundle digest" },
];

interface ArtifactHashTableProps {
  hashes: PcsHashRow[];
  canonicalDigests?: PcsCanonicalDigests;
}

export function ArtifactHashTable({ hashes, canonicalDigests }: ArtifactHashTableProps) {
  const canonicalRows =
    canonicalDigests != null
      ? CANONICAL_LABELS.map(({ key, label }) => ({
          name: label,
          digest: canonicalDigests[key] || "",
          source_artifact: key,
        })).filter((row) => row.digest.length > 0)
      : [];

  const extraHashes = hashes.filter(
    (row) => !canonicalRows.some((c) => c.digest === row.digest && c.name === row.name),
  );

  const rows = [...canonicalRows, ...extraHashes];

  return (
    <section data-testid="pcs-section-artifact-hashes">
      <h2 className="text-lg font-medium">Artifact Hashes</h2>
      {rows.length === 0 ? (
        <p className="mt-2 text-sm text-gray-600">No hashes recorded.</p>
      ) : (
        <div className="mt-3 overflow-x-auto">
          <table className="min-w-full border text-sm" data-testid="pcs-hash-table">
            <thead className="bg-gray-50">
              <tr>
                <th className="border px-3 py-2 text-left font-medium">Artifact</th>
                <th className="border px-3 py-2 text-left font-medium">Digest</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={`${row.source_artifact}-${row.name}-${row.digest}`}>
                  <td className="border px-3 py-2 text-sm">{row.name}</td>
                  <td
                    className="border px-3 py-2 font-mono text-xs break-all"
                    data-testid="pcs-hash-digest"
                  >
                    {row.digest}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
