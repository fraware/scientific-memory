import type { PcsNamedArtifact } from "@/lib/pcsTypes";

interface RuntimeReceiptViewProps {
  receipt: PcsNamedArtifact;
}

export function RuntimeReceiptView({ receipt }: RuntimeReceiptViewProps) {
  return (
    <section data-testid="pcs-section-runtime-evidence">
      <h2 className="text-lg font-medium">Runtime Evidence</h2>
      <p className="mt-1 text-sm text-gray-600">
        Status:{" "}
        <span
          className="rounded bg-gray-200 px-2 py-0.5 font-medium"
          data-testid="pcs-runtime-status"
        >
          {String(receipt.status ?? "unknown")}
        </span>
      </p>
      {receipt.summary != null && (
        <p className="mt-2 text-sm">{String(receipt.summary)}</p>
      )}
      {receipt.trace_hash != null && (
        <p className="mt-2 font-mono text-xs text-gray-700" data-testid="pcs-runtime-trace-hash">
          trace_hash: {String(receipt.trace_hash)}
        </p>
      )}
      {receipt.payload != null && (
        <pre className="mt-3 overflow-x-auto rounded border bg-gray-50 p-3 text-xs">
          {JSON.stringify(receipt.payload, null, 2)}
        </pre>
      )}
    </section>
  );
}
