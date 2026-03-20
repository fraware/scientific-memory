import Link from "next/link";
import {
  getPapersList,
  getDiffBaseline,
  getDiffCurrent,
  type DiffBaseline,
  type DiffDeclaration,
} from "@/lib/data";

export type StatusTransition = { claimId: string; from: string; to: string };

const PROOF_STATUS_RANK: Record<string, number> = {
  unparsed: 0,
  parsed: 1,
  mapped: 2,
  stubbed: 3,
  compiles_with_sorries: 4,
  machine_checked: 5,
  linked_to_kernel: 6,
  disputed: -1,
  superseded: -1,
};

function proofRank(s: string): number {
  return PROOF_STATUS_RANK[s] ?? -2;
}

export type ProofChange = {
  lean_decl: string;
  kind: "new" | "broken";
  from?: string;
  to?: string;
};

function getProofChanges(
  basePaper: DiffBaseline["papers"][0],
  currPaper: DiffBaseline["papers"][0],
): { newProofs: ProofChange[]; brokenProofs: ProofChange[] } {
  const baseDecls = (basePaper.declarations ?? []) as DiffDeclaration[];
  const currDecls = (currPaper.declarations ?? []) as DiffDeclaration[];
  if (baseDecls.length === 0 && currDecls.length === 0) {
    return { newProofs: [], brokenProofs: [] };
  }
  const baseMap = new Map(baseDecls.map((d) => [d.lean_decl, d.proof_status]));
  const currMap = new Map(currDecls.map((d) => [d.lean_decl, d.proof_status]));
  const newProofs: ProofChange[] = [];
  const brokenProofs: ProofChange[] = [];
  for (const d of currDecls) {
    const baseStatus = baseMap.get(d.lean_decl);
    if (baseStatus === undefined) {
      newProofs.push({
        lean_decl: d.lean_decl,
        kind: "new",
        to: d.proof_status,
      });
    } else if (proofRank(d.proof_status) > proofRank(baseStatus)) {
      newProofs.push({
        lean_decl: d.lean_decl,
        kind: "new",
        from: baseStatus,
        to: d.proof_status,
      });
    }
  }
  for (const d of baseDecls) {
    const currStatus = currMap.get(d.lean_decl);
    if (currStatus === undefined) {
      brokenProofs.push({
        lean_decl: d.lean_decl,
        kind: "broken",
        from: d.proof_status,
      });
    } else if (proofRank(currStatus) < proofRank(d.proof_status)) {
      brokenProofs.push({
        lean_decl: d.lean_decl,
        kind: "broken",
        from: d.proof_status,
        to: currStatus,
      });
    }
  }
  return { newProofs, brokenProofs };
}

function getStatusTransitions(
  baseStatuses: { id: string; status: string }[],
  currStatuses: { id: string; status: string }[],
): StatusTransition[] {
  const baseMap = new Map(baseStatuses.map((s) => [s.id, s.status]));
  const currMap = new Map(currStatuses.map((s) => [s.id, s.status]));
  const transitions: StatusTransition[] = [];
  for (const { id, status: to } of currStatuses) {
    const from = baseMap.get(id);
    if (from === undefined)
      transitions.push({ claimId: id, from: "", to: to || "(new)" });
    else if (from !== to) transitions.push({ claimId: id, from, to: to || "" });
  }
  for (const { id, status: from } of baseStatuses) {
    if (!currMap.has(id))
      transitions.push({ claimId: id, from: from || "", to: "(removed)" });
  }
  return transitions;
}

function diffPapers(
  baseline: DiffBaseline,
  current: DiffBaseline,
): {
  added: DiffBaseline["papers"];
  removed: DiffBaseline["papers"];
  changed: {
    paper: DiffBaseline["papers"][0];
    baseline: DiffBaseline["papers"][0];
    claimDelta: number;
    assumptionAdded: string[];
    assumptionRemoved: string[];
    assumptionTextDrift: string[];
    statusTransitions: StatusTransition[];
    newProofs: ProofChange[];
    brokenProofs: ProofChange[];
  }[];
} {
  const baseIds = new Set(baseline.papers.map((p) => p.id));
  const currIds = new Set(current.papers.map((p) => p.id));
  const added = current.papers.filter((p) => !baseIds.has(p.id));
  const removed = baseline.papers.filter((p) => !currIds.has(p.id));
  const changed: {
    paper: DiffBaseline["papers"][0];
    baseline: DiffBaseline["papers"][0];
    claimDelta: number;
    assumptionAdded: string[];
    assumptionRemoved: string[];
    assumptionTextDrift: string[];
    statusTransitions: StatusTransition[];
    newProofs: ProofChange[];
    brokenProofs: ProofChange[];
  }[] = [];
  for (const curr of current.papers) {
    if (added.some((a) => a.id === curr.id)) continue;
    const base = baseline.papers.find((p) => p.id === curr.id);
    if (!base) continue;
    const claimDelta = curr.claim_count - (base.claim_count ?? 0);
    const baseAssump = new Set(base.assumption_ids ?? []);
    const currAssump = new Set(curr.assumption_ids ?? []);
    const assumptionAdded = [...currAssump].filter((id) => !baseAssump.has(id));
    const assumptionRemoved = [...baseAssump].filter(
      (id) => !currAssump.has(id),
    );
    const baseDig = base.assumption_text_digests ?? {};
    const currDig = curr.assumption_text_digests ?? {};
    const assumptionTextDrift: string[] = [];
    for (const aid of baseAssump) {
      if (!currAssump.has(aid)) continue;
      const b = baseDig[aid];
      const c = currDig[aid];
      if (b != null && c != null && b !== c) assumptionTextDrift.push(aid);
    }
    const statusTransitions = getStatusTransitions(
      base.claim_statuses ?? [],
      curr.claim_statuses ?? [],
    );
    const { newProofs, brokenProofs } = getProofChanges(base, curr);
    const hasOtherChanges =
      claimDelta !== 0 ||
      assumptionAdded.length > 0 ||
      assumptionRemoved.length > 0 ||
      assumptionTextDrift.length > 0;
    if (
      hasOtherChanges ||
      statusTransitions.length > 0 ||
      newProofs.length > 0 ||
      brokenProofs.length > 0
    ) {
      changed.push({
        paper: curr,
        baseline: base,
        claimDelta,
        assumptionAdded,
        assumptionRemoved,
        assumptionTextDrift,
        statusTransitions,
        newProofs,
        brokenProofs,
      });
    }
  }
  return { added, removed, changed };
}

async function DiffPageByBaseline(baselineId: string) {
  const papers = await getPapersList();
  const baseline = await getDiffBaseline(baselineId);
  const current = await getDiffCurrent();
  const delta = baseline ? diffPapers(baseline, current) : null;

  return (
    <main className="mx-auto max-w-5xl p-8">
      <h1 className="text-3xl font-semibold">Diff</h1>
      <p className="mt-2 text-gray-600">
        Version-to-version changes, assumption drift, new and broken proofs,
        status transitions.
      </p>
      {!baseline && (
        <p className="mt-4 text-sm text-gray-500">
          No baseline snapshot found. Place a snapshot at{" "}
          <code className="rounded bg-gray-100 px-1">
            corpus/snapshots/last-release.json
          </code>{" "}
          to compare current corpus against it. Format:{" "}
          <code className="rounded bg-gray-100 px-1">{`{ "snapshot_at": "...", "papers": [{ "id", "claim_count", "assumption_ids": [], "assumption_text_digests": {} }] }`}</code>
        </p>
      )}

      {baseline && delta && (
        <>
          <p className="mt-2 text-sm text-gray-500">
            Comparing current corpus to baseline
            {baseline.snapshot_at ? ` (${baseline.snapshot_at})` : ""}.
          </p>
          {(baseline.title || baseline.narrative) && (
            <section className="mt-4 rounded border bg-gray-50 p-4">
              {baseline.title && (
                <h2 className="text-lg font-medium">{baseline.title}</h2>
              )}
              {baseline.narrative && (
                <p className="mt-1 text-sm text-gray-700">
                  {baseline.narrative}
                </p>
              )}
              {(baseline.highlights ?? []).length > 0 && (
                <ul className="mt-2 list-inside list-disc text-sm text-gray-700">
                  {(baseline.highlights ?? []).map((h) => (
                    <li key={h}>{h}</li>
                  ))}
                </ul>
              )}
            </section>
          )}
          {delta.added.length > 0 && (
            <section className="mt-6">
              <h2 className="text-xl font-medium text-green-700">
                Papers added
              </h2>
              <ul className="mt-2 space-y-1">
                {delta.added.map((p) => (
                  <li key={p.id}>
                    <Link
                      href={`/papers/${p.id}`}
                      className="text-blue-600 hover:underline"
                    >
                      {p.title ?? p.id}
                    </Link>
                    <span className="ml-2 text-sm text-gray-500">
                      {p.claim_count} claims
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          )}
          {delta.removed.length > 0 && (
            <section className="mt-6">
              <h2 className="text-xl font-medium text-red-700">
                Papers removed
              </h2>
              <ul className="mt-2 space-y-1">
                {delta.removed.map((p) => (
                  <li key={p.id}>
                    <span className="font-medium">{p.title ?? p.id}</span>
                    <span className="ml-2 text-sm text-gray-500">
                      {p.claim_count ?? 0} claims (baseline)
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          )}
          {delta.changed.length > 0 && (
            <section className="mt-6">
              <h2 className="text-xl font-medium">
                Changes (claim count, assumptions, status transitions)
              </h2>
              <ul className="mt-2 space-y-3">
                {delta.changed.map(
                  ({
                    paper,
                    claimDelta,
                    assumptionAdded,
                    assumptionRemoved,
                    assumptionTextDrift,
                    statusTransitions,
                    newProofs,
                    brokenProofs,
                  }) => (
                    <li key={paper.id} className="rounded border p-3">
                      <Link
                        href={`/papers/${paper.id}`}
                        className="font-medium text-blue-600 hover:underline"
                      >
                        {paper.title ?? paper.id}
                      </Link>
                      <div className="mt-1 text-sm">
                        {claimDelta !== 0 && (
                          <span
                            className={
                              claimDelta > 0
                                ? "text-green-600"
                                : "text-amber-600"
                            }
                          >
                            Claims: {claimDelta > 0 ? "+" : ""}
                            {claimDelta}
                          </span>
                        )}
                        {assumptionAdded.length > 0 && (
                          <span className="ml-2 text-green-600">
                            Assumptions added: {assumptionAdded.join(", ")}
                          </span>
                        )}
                        {assumptionRemoved.length > 0 && (
                          <span className="ml-2 text-amber-600">
                            Assumptions removed: {assumptionRemoved.join(", ")}
                          </span>
                        )}
                        {assumptionTextDrift.length > 0 && (
                          <span className="ml-2 text-purple-700">
                            Assumption text drift (same id):{" "}
                            {assumptionTextDrift.join(", ")}
                          </span>
                        )}
                      </div>
                      {statusTransitions.length > 0 && (
                        <div className="mt-2">
                          <h3 className="text-sm font-medium text-gray-700">
                            Claim status transitions
                          </h3>
                          <ul className="mt-1 list-inside list-disc space-y-0.5 text-sm">
                            {statusTransitions.map((t) => (
                              <li key={t.claimId}>
                                <Link
                                  href={`/claims/${encodeURIComponent(t.claimId)}`}
                                  className="text-blue-600 hover:underline"
                                >
                                  {t.claimId}
                                </Link>{" "}
                                {t.from ? `${t.from} → ${t.to}` : t.to}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {newProofs.length > 0 && (
                        <div className="mt-2">
                          <h3 className="text-sm font-medium text-green-700">
                            New proofs
                          </h3>
                          <ul className="mt-1 list-inside list-disc space-y-0.5 text-sm text-green-700">
                            {newProofs.map((pr) => (
                              <li key={pr.lean_decl}>
                                <Link
                                  href={`/theorem-cards/${encodeURIComponent(pr.lean_decl)}`}
                                  className="text-blue-600 hover:underline"
                                >
                                  {pr.lean_decl}
                                </Link>
                                {pr.from != null && pr.to != null
                                  ? ` (${pr.from} → ${pr.to})`
                                  : pr.to
                                    ? ` (${pr.to})`
                                    : ""}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {brokenProofs.length > 0 && (
                        <div className="mt-2">
                          <h3 className="text-sm font-medium text-red-700">
                            Broken proofs
                          </h3>
                          <ul className="mt-1 list-inside list-disc space-y-0.5 text-sm text-red-700">
                            {brokenProofs.map((pr) => (
                              <li key={pr.lean_decl}>
                                <Link
                                  href={`/theorem-cards/${encodeURIComponent(pr.lean_decl)}`}
                                  className="text-blue-600 hover:underline"
                                >
                                  {pr.lean_decl}
                                </Link>
                                {pr.from != null && pr.to != null
                                  ? ` (${pr.from} → ${pr.to})`
                                  : pr.from
                                    ? ` (was ${pr.from})`
                                    : ""}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </li>
                  ),
                )}
              </ul>
            </section>
          )}
          {delta.added.length === 0 &&
            delta.removed.length === 0 &&
            delta.changed.length === 0 && (
              <p className="mt-4 text-sm text-gray-500">
                No differences from baseline.
              </p>
            )}
        </>
      )}

      <section className="mt-8">
        <h2 className="text-xl font-medium">Current papers</h2>
        <p className="mt-1 text-sm text-gray-500">
          All papers in the corpus (current state).
        </p>
        <ul className="mt-3 space-y-2">
          {papers.map((p) => (
            <li key={p.id}>
              <Link
                href={`/papers/${p.id}`}
                className="text-blue-600 hover:underline"
              >
                {p.title || p.id}
              </Link>
              <span className="ml-2 text-sm text-gray-500">
                {p.year} · {p.id}
              </span>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}

export default async function DiffPage() {
  return DiffPageByBaseline("last-release");
}
