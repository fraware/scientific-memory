import type { PcsArtifactRegistryEntry } from "@/lib/pcsTypes";

interface Props {
  entries: PcsArtifactRegistryEntry[];
}

export function ArtifactRegistryView({ entries }: Props) {
  return (
    <section data-testid="pcs-section-artifact-registry">
      <h2 className="text-xl font-semibold">Artifact Registry</h2>
      <div className="mt-3 overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b text-gray-500">
            <tr>
              <th className="py-2 pr-4">Artifact</th>
              <th className="py-2 pr-4">Type</th>
              <th className="py-2 pr-4">Producer</th>
              <th className="py-2 pr-4">Schema</th>
              <th className="py-2 pr-4">Status</th>
              <th className="py-2 pr-4">Hash</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => (
              <tr key={entry.name} className="border-b border-gray-100 align-top">
                <td className="py-2 pr-4 font-mono text-xs">{entry.name}</td>
                <td className="py-2 pr-4">{entry.artifact_type}</td>
                <td className="py-2 pr-4">{entry.producer}</td>
                <td className="py-2 pr-4 font-mono text-xs">{entry.schema}</td>
                <td className="py-2 pr-4">{entry.status}</td>
                <td className="py-2 pr-4 font-mono text-xs break-all">{entry.hash}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {entries.map((entry) =>
        entry.semantic_checks_performed?.length ? (
          <p key={`${entry.name}-checks`} className="mt-2 text-xs text-gray-600">
            <span className="font-medium">{entry.name}</span> checks:{" "}
            {entry.semantic_checks_performed.join("; ")}
          </p>
        ) : null,
      )}
    </section>
  );
}
