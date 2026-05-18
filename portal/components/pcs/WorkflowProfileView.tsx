import type { PcsWorkflowProfileView } from "@/lib/pcsTypes";

interface WorkflowProfileViewProps {
  profile: PcsWorkflowProfileView;
}

export function WorkflowProfileView({ profile }: WorkflowProfileViewProps) {
  return (
    <section data-testid="pcs-section-workflow-profile">
      <h2 className="text-lg font-medium">Workflow Profile</h2>
      <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
        {profile.workflow_id ? (
          <>
            <dt className="font-medium text-gray-600">Workflow ID</dt>
            <dd className="break-all font-mono text-xs">{profile.workflow_id}</dd>
          </>
        ) : null}
        {profile.domain ? (
          <>
            <dt className="font-medium text-gray-600">Domain</dt>
            <dd>{profile.domain}</dd>
          </>
        ) : null}
      </dl>
      {profile.description ? (
        <p className="mt-3 text-sm text-gray-700">{profile.description}</p>
      ) : null}
      {profile.limitations_notice ? (
        <p className="mt-2 text-sm text-gray-600">{profile.limitations_notice}</p>
      ) : null}
      <ListBlock title="Runtime artifacts" items={profile.runtime_artifacts} />
      <ListBlock title="Certificate artifacts" items={profile.certificate_artifacts} />
      <ListBlock title="Required registry entries" items={profile.required_registry_entries} />
    </section>
  );
}

function ListBlock({ title, items }: { title: string; items?: string[] }) {
  if (!items?.length) return null;
  return (
    <div className="mt-4">
      <h3 className="text-sm font-medium text-gray-700">{title}</h3>
      <ul className="mt-1 list-inside list-disc text-sm text-gray-700">
        {items.map((item) => (
          <li key={item} className="font-mono text-xs">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
