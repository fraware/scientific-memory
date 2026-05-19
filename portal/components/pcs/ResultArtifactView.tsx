import type { PcsNamedArtifact } from "@/lib/pcsTypes";

import { ComputationFieldSection } from "./ComputationFieldSection";

export function ResultArtifactView({ artifact }: { artifact: PcsNamedArtifact }) {
  return (
    <ComputationFieldSection
      title="Result Artifact"
      testId="pcs-section-result-artifact"
      artifact={artifact}
      fields={[
        { label: "Result kind", key: "result_kind" },
        { label: "Path", key: "path", mono: true },
        { label: "Hash", key: "sha256", mono: true },
        { label: "Size (bytes)", key: "size_bytes" },
        { label: "Media type", key: "media_type" },
        { label: "Description", key: "description" },
        { label: "Produced by run", key: "produced_by_run" },
      ]}
    />
  );
}
