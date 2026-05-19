import type { PcsNamedArtifact } from "@/lib/pcsTypes";

import { ComputationFieldSection } from "./ComputationFieldSection";

type ViolationRow = {
  violation_id?: string;
  violation_type?: string;
  explanation?: string;
  expected_hash?: string;
  actual_hash?: string;
  responsible_component?: string;
  violating_artifact?: string;
  artifact_name?: string;
};

function violatingArtifactLabel(row: ViolationRow): string | undefined {
  if (row.violating_artifact) {
    return String(row.violating_artifact);
  }
  if (row.artifact_name) {
    return String(row.artifact_name);
  }
  const kind = String(row.violation_type ?? "");
  if (kind.includes("dataset")) {
    return "dataset_receipt.json";
  }
  if (kind.includes("environment")) {
    return "environment_receipt.json";
  }
  if (kind.includes("run_receipt") || kind.includes("run")) {
    return "computation_run_receipt.json";
  }
  if (kind.includes("result")) {
    return "result_artifact.json";
  }
  return undefined;
}

export function ComputationWitnessView({ witness }: { witness: PcsNamedArtifact }) {
  const payload = (witness.payload ?? {}) as Record<string, unknown>;
  const status = String(payload.status ?? witness.status ?? "");
  const rejected = status === "Rejected";
  const violations = Array.isArray(payload.violations)
    ? (payload.violations as ViolationRow[])
    : [];
  const resultHashes = Array.isArray(payload.result_hashes)
    ? (payload.result_hashes as string[]).join(", ")
    : undefined;

  return (
    <ComputationFieldSection
      title="Computation Witness"
      testId="pcs-section-computation-witness"
      artifact={witness}
      fields={[
        { label: "Witness ID", key: "witness_id" },
        { label: "Status", key: "status" },
        { label: "Dataset hash", key: "dataset_hash", mono: true },
        { label: "Environment hash", key: "environment_hash", mono: true },
        { label: "Run receipt hash", key: "run_receipt_hash", mono: true },
        { label: "Checker", key: "checker" },
        { label: "Checker version", key: "checker_version" },
      ]}
    >
      {resultHashes ? (
        <p className="mt-3 text-sm">
          <span className="font-medium text-gray-600">Result hashes: </span>
          <span className="font-mono text-xs">{resultHashes}</span>
        </p>
      ) : null}
      {rejected && violations.length ? (
        <div className="mt-4 rounded border border-red-200 bg-red-50 p-4" data-testid="pcs-computation-witness-failures">
          <h3 className="text-sm font-medium text-red-900">Rejected witness evidence</h3>
          <ul className="mt-3 space-y-3 text-sm">
            {violations.map((row) => (
              <li key={String(row.violation_id ?? row.violation_type)} className="rounded border border-red-100 bg-white p-3">
                <p>
                  <span className="font-medium">Failed check: </span>
                  {String(row.violation_type ?? "unknown")}
                </p>
                {violatingArtifactLabel(row) ? (
                  <p>
                    <span className="font-medium">Violating artifact: </span>
                    <span className="font-mono text-xs">{violatingArtifactLabel(row)}</span>
                  </p>
                ) : null}
                {row.violation_id ? (
                  <p>
                    <span className="font-medium">Violation ID: </span>
                    {row.violation_id}
                  </p>
                ) : null}
                {row.responsible_component ? (
                  <p>
                    <span className="font-medium">Responsible component: </span>
                    {row.responsible_component}
                  </p>
                ) : null}
                {row.expected_hash ? (
                  <p className="font-mono text-xs break-all">
                    <span className="font-sans font-medium">Expected hash: </span>
                    {row.expected_hash}
                  </p>
                ) : null}
                {row.actual_hash ? (
                  <p className="font-mono text-xs break-all">
                    <span className="font-sans font-medium">Actual hash: </span>
                    {row.actual_hash}
                  </p>
                ) : null}
                {row.explanation ? (
                  <p className="mt-1 text-gray-700">
                    <span className="font-medium">Repair hint: </span>
                    {row.explanation}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </ComputationFieldSection>
  );
}
