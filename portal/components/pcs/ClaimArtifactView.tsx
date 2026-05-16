import type { PcsClaimSection } from "@/lib/pcsTypes";

const GUARANTEE_LABELS: Record<string, string> = {
  formally_checked: "Formally checked",
  certificate_checked: "Certificate checked",
  runtime_observed: "Runtime observed",
  empirically_measured: "Empirically measured",
  human_reviewed: "Human reviewed",
  unchecked_advisory: "Unchecked advisory",
};

interface ClaimArtifactViewProps {
  claim: PcsClaimSection;
}

export function ClaimArtifactView({ claim }: ClaimArtifactViewProps) {
  const guarantees = claim.guarantee_types ?? {};
  return (
    <section data-testid="pcs-section-claim">
      <h2 className="text-lg font-medium">Claim</h2>
      <p className="mt-2 rounded border bg-gray-50 p-4 text-sm">{claim.text}</p>
      <p className="mt-2 text-sm text-gray-600">
        Status:{" "}
        <span className="rounded bg-gray-200 px-2 py-0.5 font-medium" data-testid="pcs-claim-status">
          {claim.status}
        </span>
      </p>
      <div className="mt-4">
        <h3 className="text-sm font-medium text-gray-700">Guarantee separation</h3>
        <ul className="mt-2 flex flex-wrap gap-2">
          {Object.entries(GUARANTEE_LABELS).map(([key, label]) => (
            <li key={key}>
              <span
                className={`inline-flex rounded px-2 py-0.5 text-xs font-medium ${
                  guarantees[key]
                    ? "bg-green-100 text-green-900"
                    : "bg-gray-100 text-gray-600"
                }`}
              >
                {label}: {guarantees[key] ? "yes" : "no"}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
