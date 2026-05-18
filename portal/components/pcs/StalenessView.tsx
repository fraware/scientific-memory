import type { PcsStalenessView } from "@/lib/pcsTypes";

interface Props {
  staleness: PcsStalenessView;
}

export function StalenessView({ staleness }: Props) {
  const reasons = staleness.stale_reasons ?? [];
  return (
    <section data-testid="pcs-section-staleness">
      <h2 className="text-xl font-semibold">Staleness</h2>
      <p className="mt-2 text-sm">
        Status:{" "}
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
    </section>
  );
}
