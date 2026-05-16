import type { PcsVerificationResult } from "@/lib/pcsTypes";

interface VerificationResultViewProps {
  result: PcsVerificationResult | null | undefined;
}

export function VerificationResultView({ result }: VerificationResultViewProps) {
  if (!result) {
    return (
      <section data-testid="pcs-section-verification-result">
        <h2 className="text-lg font-medium">Verification Result</h2>
        <p className="mt-2 text-sm text-amber-800" data-testid="pcs-verification-missing">
          No VerificationResult was bundled. Checks from Provability Fabric are not shown.
        </p>
      </section>
    );
  }

  const checks = result.checks ?? [];
  return (
    <section data-testid="pcs-section-verification-result">
      <h2 className="text-lg font-medium">Verification Result</h2>
      <p className="mt-1 text-sm text-gray-600">
        Status:{" "}
        <span
          className="rounded bg-gray-200 px-2 py-0.5 font-medium"
          data-testid="pcs-verification-status"
        >
          {String(result.status ?? "unknown")}
        </span>
        {result.overall_outcome != null && (
          <span className="ml-2">
            Overall:{" "}
            <span className="rounded bg-gray-200 px-2 py-0.5 font-medium">
              {result.overall_outcome}
            </span>
          </span>
        )}
      </p>
      <ul className="mt-3 space-y-2">
        {checks.map((c) => (
          <li key={c.id} className="rounded border p-3 text-sm">
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
            {c.detail != null && <p className="mt-1 text-gray-700">{c.detail}</p>}
          </li>
        ))}
      </ul>
    </section>
  );
}
