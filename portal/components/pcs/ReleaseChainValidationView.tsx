import type { PcsReleaseChainValidationView } from "@/lib/pcsTypes";

interface Props {
  validation: PcsReleaseChainValidationView;
}

export function ReleaseChainValidationView({ validation }: Props) {
  return (
    <section data-testid="pcs-section-release-chain-validation">
      <h2 className="text-xl font-semibold">Release Chain Validation</h2>
      <p className="mt-1 text-sm text-gray-600">
        {validation.validator} {validation.validator_version} · {validation.status} ·{" "}
        {validation.checked_at}
      </p>
      <ul className="mt-3 space-y-2 text-sm">
        {(validation.checks || []).map((check) => (
          <li key={check.check_id} className="rounded border border-gray-200 p-3">
            <p className="font-medium">{check.check_id}</p>
            <p className="text-gray-600">{check.description}</p>
            <p className="mt-1 font-mono text-xs">status: {check.status}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
