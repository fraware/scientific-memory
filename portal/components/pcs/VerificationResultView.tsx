import type { PcsVerificationResult } from "@/lib/pcsTypes";

interface VerificationResultViewProps {
  result: PcsVerificationResult | null | undefined;
}

function MetaRow({ label, value }: { label: string; value: string }) {
  if (!value) return null;
  const testId = `pcs-vr-${label.toLowerCase().replace(/\s+/g, "-")}`;
  return (
    <p className="text-sm text-gray-700">
      <span className="font-medium">{label}:</span>{" "}
      <span className="font-mono text-xs break-all" data-testid={testId}>
        {value}
      </span>
    </p>
  );
}

export function VerificationResultView({ result }: VerificationResultViewProps) {
  if (!result) {
    return (
      <section data-testid="pcs-section-verification-result">
        <h2 className="text-lg font-medium">Verification Result</h2>
        <p className="mt-2 text-sm text-amber-800" data-testid="pcs-verification-missing">
          No VerificationResult.v0 from Provability Fabric was bundled. External
          verification checks are not shown.
        </p>
      </section>
    );
  }

  const checks = result.checks ?? [];
  const verificationId = result.verification_id ?? result.id ?? "";

  return (
    <section data-testid="pcs-section-verification-result">
      <h2 className="text-lg font-medium">Verification Result</h2>
      <p className="mt-1 text-xs text-gray-500">Provability Fabric VerificationResult.v0</p>

      <div className="mt-3 space-y-1 rounded border bg-gray-50 p-3">
        <MetaRow label="verification_id" value={verificationId} />
        <p className="text-sm text-gray-700">
          <span className="font-medium">status:</span>{" "}
          <span
            className="rounded bg-gray-200 px-2 py-0.5 font-medium"
            data-testid="pcs-verification-status"
          >
            {String(result.status ?? "unknown")}
          </span>
          {result.overall_outcome != null && (
            <span className="ml-2">
              overall:{" "}
              <span className="rounded bg-gray-200 px-2 py-0.5 text-xs">
                {result.overall_outcome}
              </span>
            </span>
          )}
        </p>
        <MetaRow label="verifier" value={String(result.verifier ?? "")} />
        <MetaRow label="verifier_version" value={String(result.verifier_version ?? "")} />
        <MetaRow label="source_repo" value={String(result.source_repo ?? "")} />
        <MetaRow label="source_commit" value={String(result.source_commit ?? "")} />
        <MetaRow label="signature_or_digest" value={String(result.signature_or_digest ?? "")} />
      </div>

      <h3 className="mt-4 text-sm font-medium text-gray-700">checks</h3>
      <ul className="mt-2 space-y-2">
        {checks.map((c) => (
          <li key={c.id || c.name} className="rounded border p-3 text-sm">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium">{c.name}</span>
              <span
                className="rounded bg-gray-100 px-2 py-0.5 text-xs font-medium uppercase"
                data-testid="pcs-check-outcome"
              >
                {c.outcome}
              </span>
              {c.guarantee_type != null && (
                <span className="text-xs text-gray-500">{c.guarantee_type}</span>
              )}
            </div>
            {c.detail != null && c.detail !== "" && (
              <p className="mt-1 text-gray-700">{c.detail}</p>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
