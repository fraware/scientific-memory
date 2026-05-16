import type { PcsAssumption, PcsNamedArtifact } from "@/lib/pcsTypes";

interface AssumptionSetViewProps {
  assumptionSet: PcsNamedArtifact & { assumptions?: PcsAssumption[] };
}

export function AssumptionSetView({ assumptionSet }: AssumptionSetViewProps) {
  const assumptions = assumptionSet.assumptions ?? [];
  return (
    <section data-testid="pcs-section-assumptions">
      <h2 className="text-lg font-medium">Assumptions</h2>
      {assumptionSet.status != null && (
        <p className="mt-1 text-sm text-gray-600">
          Set status:{" "}
          <span className="rounded bg-gray-200 px-2 py-0.5 font-medium">
            {String(assumptionSet.status)}
          </span>
        </p>
      )}
      <ul className="mt-3 space-y-2">
        {assumptions.map((a) => (
          <li key={a.id} className="rounded border p-3 text-sm">
            <span className="font-medium">{a.id}</span>
            {a.kind != null && (
              <span className="ml-2 text-gray-500">({a.kind})</span>
            )}
            {a.status != null && (
              <span
                className="ml-2 rounded bg-gray-100 px-1.5 py-0.5 text-xs"
                data-testid="pcs-assumption-status"
              >
                {a.status}
              </span>
            )}
            <p className="mt-1 text-gray-800">{a.text}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
