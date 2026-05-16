import type { PcsHashRow } from "@/lib/pcsTypes";

interface ArtifactHashTableProps {
  hashes: PcsHashRow[];
}

export function ArtifactHashTable({ hashes }: ArtifactHashTableProps) {
  return (
    <section data-testid="pcs-section-artifact-hashes">
      <h2 className="text-lg font-medium">Artifact Hashes</h2>
      {hashes.length === 0 ? (
        <p className="mt-2 text-sm text-gray-600">No hashes recorded.</p>
      ) : (
        <div className="mt-3 overflow-x-auto">
          <table className="min-w-full border text-sm" data-testid="pcs-hash-table">
            <thead className="bg-gray-50">
              <tr>
                <th className="border px-3 py-2 text-left font-medium">Name</th>
                <th className="border px-3 py-2 text-left font-medium">Digest</th>
                <th className="border px-3 py-2 text-left font-medium">Algorithm</th>
                <th className="border px-3 py-2 text-left font-medium">Source artifact</th>
              </tr>
            </thead>
            <tbody>
              {hashes.map((row) => (
                <tr key={`${row.source_artifact}-${row.name}-${row.digest}`}>
                  <td className="border px-3 py-2 font-mono text-xs">{row.name}</td>
                  <td
                    className="border px-3 py-2 font-mono text-xs break-all"
                    data-testid="pcs-hash-digest"
                  >
                    {row.digest}
                  </td>
                  <td className="border px-3 py-2">{row.algorithm ?? "sha256"}</td>
                  <td className="border px-3 py-2 text-xs text-gray-600">
                    {row.source_artifact ?? "—"}
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
