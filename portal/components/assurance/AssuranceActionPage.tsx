import type { ReactNode } from "react";
import type { AssuranceActionModel, EvidenceClass } from "@/lib/assuranceTypes";
import { EvidenceClassBadges } from "./EvidenceClassBadges";

const DECISION_CLASSES = new Set([
  "source",
  "evidence",
  "claim",
  "proposed_action",
  "admissibility_decision",
  "review",
  "grant",
]);

const RUNTIME_CLASSES = new Set(["runtime_action", "verification_result"]);
const OUTCOME_CLASSES = new Set(["outcome"]);
const REPLICATION_CLASSES = new Set(["replication"]);
const CALIBRATION_CLASSES = new Set(["calibration_update"]);

function Section({
  title,
  testId,
  children,
}: {
  title: string;
  testId: string;
  children: ReactNode;
}) {
  return (
    <section className="mt-8" data-testid={testId}>
      <h2 className="text-lg font-medium">{title}</h2>
      <div className="mt-3 space-y-3 text-sm">{children}</div>
    </section>
  );
}

function NodeList({
  model,
  classes,
}: {
  model: AssuranceActionModel;
  classes: Set<string>;
}) {
  const nodes = model.nodes.filter((n) => classes.has(n.node_class));
  if (!nodes.length) {
    return <p className="text-gray-500">None recorded.</p>;
  }
  return (
    <ul className="space-y-3">
      {nodes.map((n) => (
        <li key={n.node_id} className="rounded border border-gray-200 p-3">
          <p className="font-medium">
            {n.node_class}: {n.summary}
          </p>
          <p className="text-xs text-gray-500">{n.node_id}</p>
          <EvidenceClassBadges classes={n.evidence_classes} />
        </li>
      ))}
    </ul>
  );
}

export function AssuranceActionPage({
  model,
}: {
  model: AssuranceActionModel;
}) {
  const authority = model.nodes.filter((n) =>
    ["proposed_action", "admissibility_decision", "review", "grant"].includes(
      n.node_class,
    ),
  );

  return (
    <main className="mx-auto max-w-5xl p-8">
      <h1 className="text-3xl font-semibold">Action {model.action_id}</h1>
      <p className="mt-2 text-sm text-gray-600">
        Assurance action chain. Presence of outcomes or calibrations does not
        rewrite claim status.
      </p>

      <Section
        title="Decision-time evidence"
        testId="assurance-decision-evidence"
      >
        <NodeList model={model} classes={DECISION_CLASSES} />
      </Section>

      <Section title="Action and authority chain" testId="assurance-authority">
        {authority.length ? (
          <ol className="list-decimal space-y-2 pl-5">
            {authority.map((n) => (
              <li key={n.node_id}>
                {n.node_class}: {n.summary}
              </li>
            ))}
          </ol>
        ) : (
          <p className="text-gray-500">None recorded.</p>
        )}
      </Section>

      <Section title="Execution and verification" testId="assurance-execution">
        <NodeList model={model} classes={RUNTIME_CLASSES} />
      </Section>

      <Section title="Realized outcome" testId="assurance-outcome">
        {model.outcomes.length ? (
          model.outcomes.map((o) => (
            <div
              key={o.outcome_id}
              className="rounded border border-gray-200 p-3"
            >
              <p className="font-medium">{o.outcome_id}</p>
              <p>Status delayed: {o.delayed_result_status ?? "unknown"}</p>
              <p>Replication: {o.replication_status ?? "unknown"}</p>
              <EvidenceClassBadges classes={o.evidence_classes} />
              {o.non_claim ? (
                <p className="mt-2 text-xs text-gray-500">{o.non_claim}</p>
              ) : null}
            </div>
          ))
        ) : (
          <NodeList model={model} classes={OUTCOME_CLASSES} />
        )}
      </Section>

      <Section title="Replication" testId="assurance-replication">
        <NodeList model={model} classes={REPLICATION_CLASSES} />
      </Section>

      <Section title="Calibration" testId="assurance-calibration">
        {model.calibrations.length ? (
          model.calibrations.map((c) => (
            <div
              key={c.calibration_id}
              className="rounded border border-gray-200 p-3"
            >
              <p className="font-medium">{c.calibration_id}</p>
              <p>Class: {c.calibration_class}</p>
              <p>Aggregation eligible: {String(c.aggregation_eligibility)}</p>
              {c.non_claim ? (
                <p className="mt-2 text-xs text-gray-500">{c.non_claim}</p>
              ) : null}
            </div>
          ))
        ) : (
          <NodeList model={model} classes={CALIBRATION_CLASSES} />
        )}
      </Section>

      <Section title="Unresolved gaps" testId="assurance-gaps">
        {model.gaps.length ? (
          <ul className="list-disc space-y-1 pl-5">
            {model.gaps.map((g) => (
              <li key={g.gap_id}>
                {g.gap_id}: {g.reason}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-500">No gaps listed.</p>
        )}
      </Section>

      <Section title="Guarantee labels" testId="assurance-guarantees">
        <p className="text-gray-600">
          Aggregate evidence classes present on this action. Lower classes are
          never promoted.
        </p>
        <EvidenceClassBadges
          classes={[
            ...new Set(
              model.nodes.flatMap(
                (n) => (n.evidence_classes ?? []) as EvidenceClass[],
              ),
            ),
          ]}
        />
      </Section>

      <Section title="Chronology" testId="assurance-chronology">
        <ol className="list-decimal space-y-2 pl-5">
          {model.chronology.map((c) => (
            <li key={c.node_id}>
              <span className="text-xs text-gray-500">{c.created_at}</span>{" "}
              {c.node_class}: {c.summary}
            </li>
          ))}
        </ol>
      </Section>
    </main>
  );
}
