import type { PcsNamedArtifact } from "@/lib/pcsTypes";

import { ComputationFieldSection } from "./ComputationFieldSection";

export function DatasetReceiptView({ receipt }: { receipt: PcsNamedArtifact }) {
  const payload = (receipt.payload ?? {}) as Record<string, unknown>;
  const files = Array.isArray(payload.files) ? payload.files : [];

  return (
    <ComputationFieldSection
      title="Dataset Receipt"
      testId="pcs-section-dataset-receipt"
      artifact={receipt}
      fields={[
        { label: "Dataset ID", key: "dataset_id" },
        { label: "Dataset version", key: "dataset_version" },
        { label: "Aggregate hash", key: "aggregate_hash", mono: true },
        { label: "Source URI", key: "source_uri", mono: true },
        { label: "License", key: "license" },
      ]}
    >
      {files.length ? (
        <div className="mt-4">
          <h3 className="text-sm font-medium text-gray-700">Files</h3>
          <ul className="mt-2 space-y-2 text-sm">
            {files.map((file, index) => {
              const row = file as Record<string, unknown>;
              const path = String(row.path ?? `file-${index}`);
              return (
                <li key={path} className="rounded border bg-gray-50 p-2 font-mono text-xs">
                  <span className="block">{path}</span>
                  <span className="block text-gray-600">{String(row.sha256 ?? "")}</span>
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}
    </ComputationFieldSection>
  );
}
