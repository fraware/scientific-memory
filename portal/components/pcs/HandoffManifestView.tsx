import type { PcsHandoffManifestView } from "@/lib/pcsTypes";

interface HandoffManifestViewProps {
  handoffs: PcsHandoffManifestView[];
}

export function HandoffManifestView({ handoffs }: HandoffManifestViewProps) {
  if (!handoffs.length) {
    return null;
  }
  return (
    <section data-testid="pcs-handoff-manifests">
      <h2 className="text-xl font-semibold">Handoff manifests</h2>
      <ul className="mt-4 space-y-4">
        {handoffs.map((handoff) => (
          <li
            key={handoff.handoff_id ?? handoff.manifest_path}
            className="rounded border border-gray-200 p-4"
          >
            <h3 className="font-mono text-sm font-medium">{handoff.handoff_id}</h3>
            <dl className="mt-2 grid grid-cols-2 gap-2 text-sm">
              <dt className="text-gray-500">Kind</dt>
              <dd className="font-mono text-xs">{handoff.handoff_kind ?? "—"}</dd>
              <dt className="text-gray-500">From</dt>
              <dd className="font-mono text-xs">{handoff.from_component ?? "—"}</dd>
              <dt className="text-gray-500">To</dt>
              <dd className="font-mono text-xs">{handoff.to_component ?? "—"}</dd>
              <dt className="text-gray-500">Status</dt>
              <dd className="font-mono text-xs">{handoff.status ?? "—"}</dd>
              <dt className="text-gray-500">Source commit</dt>
              <dd className="font-mono text-xs">{handoff.source_commit ?? "—"}</dd>
            </dl>
            {handoff.input_artifacts?.length ? (
              <HandoffArtifactList title="Inputs" items={handoff.input_artifacts} />
            ) : null}
            {handoff.expected_outputs?.length ? (
              <HandoffArtifactList title="Expected outputs" items={handoff.expected_outputs} />
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  );
}

function HandoffArtifactList({
  title,
  items,
}: {
  title: string;
  items: { name: string; artifact_type?: string; sha256?: string }[];
}) {
  return (
    <div className="mt-3">
      <p className="text-sm font-medium text-gray-700">{title}</p>
      <ul className="mt-1 space-y-1 font-mono text-xs">
        {items.map((item) => (
          <li key={item.name}>
            {item.name}
            {item.sha256 ? ` · ${item.sha256}` : ""}
          </li>
        ))}
      </ul>
    </div>
  );
}
