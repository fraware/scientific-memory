import type { PcsNamedArtifact } from "@/lib/pcsTypes";

import { ComputationFieldSection } from "./ComputationFieldSection";

export function EnvironmentReceiptView({ receipt }: { receipt: PcsNamedArtifact }) {
  const payload = (receipt.payload ?? {}) as Record<string, unknown>;
  const runtimes = Array.isArray(payload.language_runtimes)
    ? (payload.language_runtimes as string[]).join(", ")
    : undefined;
  const packages = Array.isArray(payload.packages)
    ? (payload.packages as string[]).join(", ")
    : undefined;

  return (
    <ComputationFieldSection
      title="Environment Receipt"
      testId="pcs-section-environment-receipt"
      artifact={receipt}
      fields={[
        { label: "Environment kind", key: "environment_kind" },
        { label: "OS", key: "os" },
        { label: "Architecture", key: "architecture" },
        { label: "Container image", key: "container_image" },
        { label: "Container digest", key: "container_digest", mono: true },
        { label: "Hardware summary", key: "hardware_summary" },
      ]}
    >
      {runtimes ? (
        <p className="mt-3 text-sm">
          <span className="font-medium text-gray-600">Language runtimes: </span>
          {runtimes}
        </p>
      ) : null}
      {packages ? (
        <p className="mt-2 text-sm">
          <span className="font-medium text-gray-600">Packages: </span>
          {packages}
        </p>
      ) : null}
    </ComputationFieldSection>
  );
}
