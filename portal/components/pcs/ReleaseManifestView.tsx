import type { PcsReleaseManifestView } from "@/lib/pcsTypes";

interface Props {
  manifest: PcsReleaseManifestView;
}

export function ReleaseManifestView({ manifest }: Props) {
  const rows: { label: string; value?: string }[] = [
    { label: "Release ID", value: manifest.release_id },
    { label: "Candidate", value: manifest.release_candidate },
    { label: "Status", value: manifest.release_status },
    { label: "Profile", value: manifest.validation_profile },
    { label: "Generated", value: manifest.generated_at },
    { label: "Manifest hash", value: manifest.manifest_hash },
  ];
  return (
    <section data-testid="pcs-section-release-manifest">
      <h2 className="text-xl font-semibold">Release Manifest</h2>
      <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
        {rows.map((row) => (
          <div key={row.label}>
            <dt className="text-gray-500">{row.label}</dt>
            <dd className="break-all font-mono text-xs">{row.value || "—"}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
