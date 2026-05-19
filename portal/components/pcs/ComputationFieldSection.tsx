import type { PcsNamedArtifact } from "@/lib/pcsTypes";

type FieldSpec = { label: string; key: string; mono?: boolean };

function Field({
  label,
  value,
  mono,
}: {
  label: string;
  value?: string;
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

function payloadValue(payload: Record<string, unknown>, key: string): string | undefined {
  const value = payload[key];
  if (value === null || value === undefined) return undefined;
  if (typeof value === "string") return value;
  if (typeof value === "number") return String(value);
  if (Array.isArray(value)) return value.map(String).join(", ");
  return JSON.stringify(value);
}

export function ComputationFieldSection({
  title,
  testId,
  artifact,
  fields,
  children,
}: {
  title: string;
  testId: string;
  artifact: PcsNamedArtifact;
  fields: FieldSpec[];
  children?: React.ReactNode;
}) {
  const payload = (artifact.payload ?? {}) as Record<string, unknown>;

  return (
    <section className="rounded border border-gray-200 p-4" data-testid={testId}>
      <h2 className="text-lg font-medium">{title}</h2>
      <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
        {fields.map((field) => (
          <Field
            key={field.key}
            label={field.label}
            value={payloadValue(payload, field.key)}
            mono={field.mono}
          />
        ))}
      </dl>
      {children}
    </section>
  );
}
