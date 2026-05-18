import type { PcsArtifactRegistryEntry } from "@/lib/pcsTypes";

interface Props {
  entries: PcsArtifactRegistryEntry[];
}

const ADMISSION_STYLES: Record<string, string> = {
  passed: "bg-green-100 text-green-800 border-green-200",
  warning: "bg-amber-100 text-amber-900 border-amber-200",
  failed: "bg-red-100 text-red-800 border-red-200",
  deferred: "bg-gray-100 text-gray-700 border-gray-200",
  not_applicable: "bg-slate-100 text-slate-600 border-slate-200",
};

export function ArtifactRegistryView({ entries }: Props) {
  return (
    <section data-testid="pcs-section-artifact-registry">
      <h2 className="text-xl font-semibold">Artifact Registry</h2>
      <p className="mt-1 text-sm text-gray-600">
        Per-artifact admission against the PCS ArtifactRegistry.v0 specification and release-chain
        checks.
      </p>
      <ul className="mt-4 space-y-6">
        {entries.map((entry) => (
          <li
            key={entry.name}
            className="rounded border border-gray-200 p-4"
            data-testid={`pcs-registry-entry-${entry.name}`}
          >
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="font-mono text-sm font-medium">{entry.name}</h3>
              <AdmissionBadge status={entry.admission_status ?? entry.registry_admission_result} />
            </div>
            <RegistryFieldGrid entry={entry} />
          </li>
        ))}
      </ul>
    </section>
  );
}

function AdmissionBadge({ status }: { status?: string }) {
  const key = (status ?? "deferred").toLowerCase().replace(/\s+/g, "_");
  const style = ADMISSION_STYLES[key] ?? ADMISSION_STYLES.deferred;
  return (
    <span
      className={`rounded border px-2 py-0.5 text-xs font-medium uppercase tracking-wide ${style}`}
      data-testid="pcs-registry-admission-badge"
    >
      {key.replace(/_/g, " ")}
    </span>
  );
}

function RegistryFieldGrid({ entry }: { entry: PcsArtifactRegistryEntry }) {
  const rows: { label: string; value: string }[] = [
    { label: "artifact_type", value: entry.artifact_type },
    { label: "schema", value: entry.schema },
    { label: "schema_owner", value: entry.schema_owner ?? "" },
    { label: "runtime_producer", value: entry.runtime_producer ?? "" },
    {
      label: "allowed_runtime_producers",
      value: (entry.allowed_runtime_producers ?? []).join(", "),
    },
    { label: "producer", value: entry.producer },
    {
      label: "allowed_statuses",
      value: (entry.allowed_statuses ?? []).join(", "),
    },
    { label: "actual_status", value: entry.actual_status ?? entry.status },
    { label: "source_repo", value: entry.source_repo },
    { label: "source_commit", value: entry.source_commit },
    { label: "hash", value: entry.hash },
    {
      label: "semantic_checks",
      value: (entry.semantic_checks ?? []).join("; "),
    },
    {
      label: "semantic_checks_performed",
      value: (entry.semantic_checks_performed ?? []).join("; "),
    },
    {
      label: "required_release_fields_present",
      value: (entry.required_release_fields_present ?? []).join(", "),
    },
    {
      label: "required_release_fields_missing",
      value: (entry.required_release_fields_missing ?? []).join(", "),
    },
    {
      label: "registry_admission_result",
      value: entry.registry_admission_result ?? entry.status,
    },
    {
      label: "consumer_repos",
      value: (entry.consumer_repos ?? []).join(", "),
    },
    {
      label: "canonical_hash_required",
      value: String(entry.canonical_hash_required ?? false),
    },
    {
      label: "release_mode_required",
      value: String(entry.release_mode_required ?? false),
    },
  ];

  return (
    <dl className="mt-3 grid grid-cols-1 gap-2 text-sm md:grid-cols-2">
      {rows.map((row) => (
        <div key={row.label} className="min-w-0">
          <dt className="text-gray-500">{row.label}</dt>
          <dd
            className="font-mono text-xs break-all"
            data-testid={`pcs-registry-${entry.name}-${row.label}`}
          >
            {row.value || "—"}
          </dd>
        </div>
      ))}
    </dl>
  );
}

function motionDiv({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <div className={className}>{children}</div>;
}
