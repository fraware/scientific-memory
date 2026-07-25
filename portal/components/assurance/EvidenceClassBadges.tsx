import type { EvidenceClass } from "@/lib/assuranceTypes";

const GUARANTEE_LABELS: Record<EvidenceClass, string> = {
  formally_checked: "Formally checked",
  certificate_checked: "Certificate checked",
  runtime_observed: "Runtime observed",
  empirically_measured: "Empirically measured",
  human_reviewed: "Human reviewed",
  unchecked_advisory: "Unchecked advisory",
};

const ALL: EvidenceClass[] = [
  "formally_checked",
  "certificate_checked",
  "runtime_observed",
  "empirically_measured",
  "human_reviewed",
  "unchecked_advisory",
];

export function EvidenceClassBadges({
  classes,
}: {
  classes?: EvidenceClass[];
}) {
  const present = new Set(classes ?? []);
  return (
    <ul
      className="mt-2 flex flex-wrap gap-2"
      data-testid="assurance-evidence-classes"
    >
      {ALL.map((key) => (
        <li key={key}>
          <span
            className={`inline-flex rounded px-2 py-0.5 text-xs font-medium ${
              present.has(key)
                ? "bg-green-100 text-green-900"
                : "bg-gray-100 text-gray-600"
            }`}
          >
            {GUARANTEE_LABELS[key]}: {present.has(key) ? "yes" : "no"}
          </span>
        </li>
      ))}
    </ul>
  );
}
