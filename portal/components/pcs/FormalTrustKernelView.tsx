import type { PcsFormalTrustKernelView } from "@/lib/pcsTypes";

type FormalCheckRow = {
  obligation_id?: string;
  predicate?: string;
  lean_theorem?: string;
  status?: string;
  source_artifacts?: string[];
  checked_at?: string;
  lean_version?: string;
  result?: string;
  trust_boundary_invariant?: string;
  formal_scope?: string;
  expected?: string;
  actual?: string;
  responsible_component?: string;
  repair_hint?: string;
  pf_explain?: string;
};

function isFailed(row: FormalCheckRow): boolean {
  return row.result === "failed" || row.status === "Rejected";
}

export function FormalTrustKernelView({ kernel }: { kernel: PcsFormalTrustKernelView }) {
  const checks = (kernel.lean_check_results ?? []) as FormalCheckRow[];
  const failed = checks.filter(isFailed);
  const passed = checks.filter((row) => !isFailed(row));

  return (
    <section
      className="rounded-lg border border-indigo-200 bg-indigo-50/40 p-6"
      data-testid="pcs-section-formal-trust-kernel"
    >
      <h2 className="text-xl font-semibold text-indigo-950">
        {kernel.title ?? "Formal Trust Kernel"}
      </h2>
      <p className="mt-2 text-sm text-indigo-900">{kernel.what_was_checked}</p>

      <KernelSummary kernel={kernel} />

      {kernel.trust_boundary_invariants?.length ? (
        <InvariantsList items={kernel.trust_boundary_invariants} />
      ) : null}

      {kernel.proof_obligations?.length ? (
        <div className="mt-6">
          <h3 className="text-sm font-semibold text-gray-800">Proof obligations</h3>
          <ul className="mt-2 space-y-3">
            {(kernel.proof_obligations as FormalCheckRow[]).map((row) => (
              <li key={String(row.obligation_id)} className="rounded border bg-white p-3 text-sm">
                <p>
                  <span className="font-medium">Obligation: </span>
                  <span className="font-mono text-xs">{row.obligation_id}</span>
                </p>
                <p>
                  <span className="font-medium">Predicate: </span>
                  {row.predicate}
                </p>
                <p>
                  <span className="font-medium">Lean theorem: </span>
                  <span className="font-mono text-xs">{row.lean_theorem}</span>
                </p>
                {row.trust_boundary_invariant ? (
                  <p className="mt-1 text-gray-700">{row.trust_boundary_invariant}</p>
                ) : null}
                {row.source_artifacts?.length ? (
                  <p className="mt-1 font-mono text-xs text-gray-600">
                    Artifacts: {row.source_artifacts.join(", ")}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {passed.length ? <PassedChecks checks={passed} /> : null}
      {failed.length ? <FailedChecks checks={failed} pfExplain={kernel.pf_explain} /> : null}

      {kernel.formal_scope ? (
        <div className="mt-6 rounded border border-gray-200 bg-white p-4">
          <h3 className="text-sm font-semibold text-gray-800">Formal scope</h3>
          <p className="mt-2 text-sm text-gray-700">{kernel.formal_scope}</p>
        </div>
      ) : null}

      {kernel.formal_non_claims?.length ? (
        <div className="mt-6 rounded border border-amber-200 bg-amber-50 p-4" data-testid="pcs-formal-non-claims">
          <h3 className="text-sm font-semibold text-amber-950">Formal non-claims</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-950">
            {kernel.formal_non_claims.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}

function KernelSummary({ kernel }: { kernel: PcsFormalTrustKernelView }) {
  return (
    <dl className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
      {kernel.overall_status ? (
        <>
          <dt className="font-medium text-gray-600">Overall status</dt>
          <dd>{kernel.overall_status}</dd>
        </>
      ) : null}
      {kernel.lean_version ? (
        <>
          <dt className="font-medium text-gray-600">Lean version</dt>
          <dd className="font-mono text-xs">{kernel.lean_version}</dd>
        </>
      ) : null}
      {kernel.checked_at ? (
        <>
          <dt className="font-medium text-gray-600">Checked at</dt>
          <dd>{kernel.checked_at}</dd>
        </>
      ) : null}
      {kernel.checker ? (
        <>
          <dt className="font-medium text-gray-600">Checker</dt>
          <dd>
            {kernel.checker}
            {kernel.checker_version ? ` ${kernel.checker_version}` : ""}
          </dd>
        </>
      ) : null}
      {kernel.theorems_checked?.length ? (
        <>
          <dt className="font-medium text-gray-600">Theorems checked</dt>
          <dd className="font-mono text-xs">{kernel.theorems_checked.join(", ")}</dd>
        </>
      ) : null}
      {kernel.artifacts_used?.length ? (
        <>
          <dt className="font-medium text-gray-600">Artifacts used</dt>
          <dd className="font-mono text-xs">{kernel.artifacts_used.join(", ")}</dd>
        </>
      ) : null}
    </dl>
  );
}

function InvariantsList({ items }: { items: string[] }) {
  return (
    <div className="mt-4">
      <h3 className="text-sm font-semibold text-gray-800">PCS trust-boundary invariants</h3>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-gray-700">
        {items.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
    </div>
  );
}

function PassedChecks({ checks }: { checks: FormalCheckRow[] }) {
  return (
    <div className="mt-6">
      <h3 className="text-sm font-semibold text-gray-800">Lean check results</h3>
      <ul className="mt-2 space-y-2 text-sm">
        {checks.map((row) => (
          <li key={String(row.obligation_id)} className="rounded border border-green-100 bg-green-50 p-3">
            <p className="font-mono text-xs">{row.lean_theorem}</p>
            <p>
              {row.result ?? row.status} · {row.checked_at ?? ""} · {row.lean_version ?? ""}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}

function FailedChecks({
  checks,
  pfExplain,
}: {
  checks: FormalCheckRow[];
  pfExplain?: string | null;
}) {
  return (
    <div className="mt-6 rounded border border-red-200 bg-red-50 p-4" data-testid="pcs-formal-check-failures">
      <h3 className="text-sm font-semibold text-red-900">Failed formal checks</h3>
      <ul className="mt-3 space-y-3 text-sm">
        {checks.map((row) => (
          <li key={String(row.obligation_id)} className="rounded border border-red-100 bg-white p-3">
            <p>
              <span className="font-medium">Theorem: </span>
              <span className="font-mono text-xs">{row.lean_theorem}</span>
            </p>
            <p>
              <span className="font-medium">Obligation: </span>
              {row.obligation_id}
            </p>
            {row.source_artifacts?.length ? (
              <p>
                <span className="font-medium">Source artifacts: </span>
                <span className="font-mono text-xs">{row.source_artifacts.join(", ")}</span>
              </p>
            ) : null}
            {row.expected ? (
              <p className="font-mono text-xs break-all">
                <span className="font-sans font-medium">Expected: </span>
                {row.expected}
              </p>
            ) : null}
            {row.actual ? (
              <p className="font-mono text-xs break-all">
                <span className="font-sans font-medium">Actual: </span>
                {row.actual}
              </p>
            ) : null}
            {row.responsible_component ? (
              <p>
                <span className="font-medium">Responsible component: </span>
                {row.responsible_component}
              </p>
            ) : null}
            {row.repair_hint ? (
              <p>
                <span className="font-medium">Repair hint: </span>
                {row.repair_hint}
              </p>
            ) : null}
            {row.pf_explain ? (
              <p className="mt-1 text-gray-700">
                <span className="font-medium">PF explain: </span>
                {row.pf_explain}
              </p>
            ) : null}
          </li>
        ))}
      </ul>
      {pfExplain ? (
        <p className="mt-3 text-sm text-red-900">
          <span className="font-medium">PF explain (release): </span>
          {pfExplain}
        </p>
      ) : null}
    </div>
  );
}
