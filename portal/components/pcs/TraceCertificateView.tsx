import type { PcsNamedArtifact } from "@/lib/pcsTypes";

interface TraceCertificateViewProps {
  certificate: PcsNamedArtifact;
}

export function TraceCertificateView({ certificate }: TraceCertificateViewProps) {
  return (
    <section data-testid="pcs-section-temporal-certificate">
      <h2 className="text-lg font-medium">Temporal Certificate</h2>
      <p className="mt-1 text-sm text-gray-600">
        Status:{" "}
        <span
          className="rounded bg-gray-200 px-2 py-0.5 font-medium"
          data-testid="pcs-certificate-status"
        >
          {String(certificate.status ?? "unknown")}
        </span>
      </p>
      {certificate.summary != null && (
        <p className="mt-2 text-sm">{String(certificate.summary)}</p>
      )}
      {certificate.payload != null && (
        <pre className="mt-3 overflow-x-auto rounded border bg-gray-50 p-3 text-xs">
          {JSON.stringify(certificate.payload, null, 2)}
        </pre>
      )}
    </section>
  );
}
