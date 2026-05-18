import type { PcsNamedArtifact } from "@/lib/pcsTypes";

interface NamedProtocolArtifactViewProps {
  title: string;
  testId: string;
  artifact: PcsNamedArtifact;
}

export function NamedProtocolArtifactView({
  title,
  testId,
  artifact,
}: NamedProtocolArtifactViewProps) {
  const payload = artifact.payload as Record<string, unknown> | undefined;
  const semanticChecks = Array.isArray(payload?.semantic_checks)
    ? (payload.semantic_checks as string[])
    : [];
  const limitations = Array.isArray(payload?.limitations)
    ? (payload.limitations as string[])
    : [];

  return (
    <section className="rounded border border-gray-200 p-4" data-testid={testId}>
      <h2 className="text-lg font-medium">{title}</h2>
      <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
        <Field label="Artifact type" value={String(artifact.artifact_type ?? "")} />
        <Field label="ID" value={artifact.id} />
        <Field label="Schema" value={String(artifact.schema_version ?? "")} />
        <Field label="Status" value={String(artifact.status ?? "")} />
        <Field label="Producer" value={String(payload?.producer ?? "")} />
        <Field label="Source repo" value={artifact.source_repo} />
        <Field label="Source commit" value={artifact.source_commit} mono />
        <Field
          label="Hash"
          value={String(artifact.signature_or_digest ?? "")}
          mono
        />
      </dl>
      {artifact.summary ? (
        <p className="mt-2 text-sm text-gray-700">{artifact.summary}</p>
      ) : null}
      {semanticChecks.length ? (
        <ListBlock title="Semantic checks" items={semanticChecks} />
      ) : null}
      {limitations.length ? (
        <ListBlock title="Limitations" items={limitations} />
      ) : null}
      {payload ? (
        <pre className="mt-3 max-h-96 overflow-x-auto rounded border bg-gray-50 p-3 text-xs">
          {JSON.stringify(payload, null, 2)}
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
      <h3 className="text-sm font-medium text-gray-700">{title}</h3>
      <ul className="mt-1 list-inside list-disc text-sm text-gray-700">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
