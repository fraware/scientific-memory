import type { PcsStalenessView } from "@/lib/pcsTypes";

interface Props {
  staleness: PcsStalenessView;
}

const STATE_STYLES: Record<string, string> = {
  current: "text-green-700",
  stale: "text-amber-700",
  superseded: "text-blue-700",
  withdrawn: "text-red-700",
  revalidated: "text-emerald-700",
};

export function StalenessView({ staleness }: Props) {
  const reasons = staleness.stale_reasons ?? [];
  const claimState = staleness.claim_state ?? (staleness.stale ? "stale" : "current");
  const stateClass = STATE_STYLES[claimState] ?? "text-gray-800";

  return (
    <section data-testid="pcs-section-staleness">
      <h2 className="text-xl font-semibold">Staleness</h2>
      <p className="mt-2 text-sm">
        Claim state:{" "}
        <span className={`font-medium uppercase tracking-wide ${stateClass}`}>{claimState}</span>
        {" · "}
        Dependency drift:{" "}
        <span className={staleness.stale ? "font-medium text-amber-700" : "font-medium text-green-700"}>
          {staleness.stale ? "Stale" : "Fresh"}
        </span>
      </p>
      {reasons.length > 0 ? (
        <ul className="mt-2 list-inside list-disc text-sm text-gray-700">
          {reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-gray-600">No stale dependency signals detected.</p>
      )}
      {staleness.repair_hint ? (
        <p className="mt-3 rounded border border-amber-100 bg-amber-50 p-3 text-sm text-amber-900">
          <span className="font-medium">Repair hint:</span> {staleness.repair_hint}
        </p>
      ) : null}
      {staleness.recommended_action ? (
        <p className="mt-3 rounded border border-blue-100 bg-blue-50 p-3 text-sm text-blue-900">
          <span className="font-medium">Recommended action:</span> {staleness.recommended_action}
        </p>
      ) : null}
    </section>
  );
}
