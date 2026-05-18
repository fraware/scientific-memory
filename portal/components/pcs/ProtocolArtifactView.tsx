import type { PcsProtocolArtifact } from "@/lib/pcsTypes";

interface ProtocolArtifactViewProps {
  artifact: PcsProtocolArtifact;
}

const TYPE_LABELS: Record<string, string> = {
  "ToolUseTrace.v0": "Tool use trace",
  "ToolUseCertificate.v0": "Tool use certificate",
  "WorkflowProfile.v0": "Workflow profile",
};

/** Generic renderer for manifest-listed protocol artifacts (workflow-specific or unknown types). */
export function ProtocolArtifactView({ artifact }: ProtocolArtifactViewProps) {
  const title =
    TYPE_LABELS[artifact.artifact_type] ??
    artifact.artifact_type.replace(/\.v0$/, "").replaceAll("_", " ");

  const payload = (artifact.payload ?? {}) as Record<string, unknown>;
  const schema =
    typeof payload.schema === "string"
      ? payload.schema
      : typeof artifact.schema_version === "string"
        ? artifact.schema_version
        : "";
  const producer = typeof payload.producer === "string" ? payload.producer : "";
  const semanticChecks = Array.isArray(payload.semantic_checks)
    ? (payload.semantic_checks as string[])
    : [];
  const limitations = Array.isArray(payload.limitations)
    ? (payload.limitations as string[])
    : [];

  return (
    <section
      className="rounded border border-gray-200 p-4"
      data-testid={`pcs-protocol-artifact-${artifact.artifact_type}`}
    >
      <h3 className="text-base font-medium">{title}</h3>
      <p className="mt-1 font-mono text-xs text-gray-500">{artifact.name}</p>
      <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
        <Field label="Artifact type" value={artifact.artifact_type} />
        <Field label="Schema" value={schema} />
        <Field label="Status" value={artifact.status} />
        <Field label="Producer" value={producer} />
        <Field label="ID" value={artifact.id} />
        <Field label="Hash" value={artifact.hash ?? artifact.signature_or_digest} mono />
        <Field label="Source repo" value={artifact.source_repo} />
        <Field label="Source commit" value={artifact.source_commit} mono />
      </dl>
      {semanticChecks.length ? (
        <ListBlock title="Semantic checks" items={semanticChecks} />
      ) : null}
      {limitations.length ? (
        <ListBlock title="Limitations" items={limitations} />
      ) : null}
      {artifact.payload ? (
        <pre className="mt-3 max-h-96 overflow-x-auto rounded border bg-gray-50 p-3 text-xs">
          {JSON.stringify(artifact.payload, null, 2)}
        </pre>
      ) : null}
    </section>
  );
}

function Field({
  label,
  value,
  mono,
}: {
  label: string;
  value?: string | null;
  mono?: boolean;
}) {
  if (!value) return null;
  return (
    <>
      <dt className="font-medium text-gray-600">{label}</dt>
      <dd className={mono ? "break-all font-mono text-xs" : undefined}>{value}</dd>
    </>
  );
}

function ListBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="mt-4">
      <h4 className="text-sm font-medium text-gray-700">{title}</h4>
      <ul className="mt-1 list-inside list-disc text-sm text-gray-700">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
