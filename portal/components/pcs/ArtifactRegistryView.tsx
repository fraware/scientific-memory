import type { PcsArtifactRegistryEntry } from "@/lib/pcsTypes";

interface Props {
  entries: PcsArtifactRegistryEntry[];
}

export function ArtifactRegistryView({ entries }: Props) {
  return (
    <section data-testid="pcs-section-artifact-registry">
      <h2 className="text-xl font-semibold">Artifact Registry</h2>
      <RegistryTable entries={entries} />
    </section>
  );
}

function RegistryTable({ entries }: { entries: PcsArtifactRegistryEntry[] }) {
  return (
    <div className="mt-3 overflow-x-auto">
      <table className="min-w-full text-left text-sm">
        <thead className="border-b text-gray-500">
          <tr>
            <th className="py-2 pr-4">Artifact</th>
            <th className="py-2 pr-4">Type</th>
            <th className="py-2 pr-4">Producer</th>
            <th className="py-2 pr-4">Admission</th>
            <th className="py-2 pr-4">Hash</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr key={entry.name} className="border-b border-gray-100 align-top">
              <td className="py-2 pr-4 font-mono text-xs">{entry.name}</td>
              <td className="py-2 pr-4">{entry.artifact_type}</td>
              <td className="py-2 pr-4">{entry.producer}</td>
              <td className="py-2 pr-4">{entry.registry_admission_result ?? entry.status}</td>
              <td className="py-2 pr-4 font-mono text-xs break-all">{entry.hash}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {entries.map((entry) => (
        <RegistryEntryDetail key={`${entry.name}-detail`} entry={entry} />
      ))}
    </div>
  );
}

function RegistryEntryDetail({ entry }: { entry: PcsArtifactRegistryEntry }) {
  const missing = entry.required_release_fields_missing ?? [];
  const checks = [
    ...(entry.semantic_checks ?? []),
    ...(entry.semantic_checks_performed ?? []),
  ];
  if (!checks.length && !missing.length) {
    return null;
  }
  return (
    <p className="mt-2 text-xs text-gray-600">
      <span className="font-medium">{entry.name}</span>
      {checks.length ? ` checks: ${checks.join("; ")}` : ""}
      {missing.length ? ` missing fields: ${missing.join(", ")}` : ""}
    </p>
  );
}
