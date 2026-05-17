import type { PcsNamedArtifact } from "@/lib/pcsTypes";

interface EvidenceBundleViewProps {
  evidence: PcsNamedArtifact;
}

export function EvidenceBundleView({ evidence }: EvidenceBundleViewProps) {
  if (!evidence?.id && !evidence?.signature_or_digest) {
    return null;
  }
  return (
    <section data-testid="pcs-section-evidence-bundle">
      <h2 className="text-lg font-medium">Evidence Bundle</h2>
      {evidence.id != null && (
        <p className="mt-1 text-sm text-gray-600">
          ID: <span className="font-mono text-xs">{String(evidence.id)}</span>
        </p>
      )}
      {evidence.status != null && (
        <p className="mt-1 text-sm text-gray-600">
          Status:{" "}
          <span className="rounded bg-gray-200 px-2 py-0.5 font-medium">
            {String(evidence.status)}
          </span>
        </p>
      )}
      {evidence.payload != null && (
        <pre className="mt-3 overflow-x-auto rounded border bg-gray-50 p-3 text-xs">
          {JSON.stringify(evidence.payload, null, 2)}
        </pre>
      )}
    </section>
  );
}
