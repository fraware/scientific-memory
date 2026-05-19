import type { PcsNamedArtifact } from "@/lib/pcsTypes";

import { ComputationFieldSection } from "./ComputationFieldSection";

export function ComputationRunReceiptView({ receipt }: { receipt: PcsNamedArtifact }) {
  const payload = (receipt.payload ?? {}) as Record<string, unknown>;
  const resultRefs = Array.isArray(payload.result_artifact_refs)
    ? (payload.result_artifact_refs as string[]).join(", ")
    : undefined;

  return (
    <ComputationFieldSection
      title="Computation Run Receipt"
      testId="pcs-section-computation-run-receipt"
      artifact={receipt}
      fields={[
        { label: "Command", key: "command", mono: true },
        { label: "Code repo", key: "code_repo", mono: true },
        { label: "Code commit", key: "code_commit", mono: true },
        { label: "Dataset receipt ref", key: "dataset_receipt_ref" },
        { label: "Environment receipt ref", key: "environment_receipt_ref" },
        { label: "Exit code", key: "exit_code" },
        { label: "Started at", key: "started_at" },
        { label: "Completed at", key: "completed_at" },
        { label: "Stdout hash", key: "stdout_hash", mono: true },
        { label: "Stderr hash", key: "stderr_hash", mono: true },
      ]}
    >
      {resultRefs ? (
        <p className="mt-3 text-sm">
          <span className="font-medium text-gray-600">Result artifact refs: </span>
          <span className="font-mono text-xs">{resultRefs}</span>
        </p>
      ) : null}
    </ComputationFieldSection>
  );
}
