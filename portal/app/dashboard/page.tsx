import Link from "next/link";
import { getCoverageDashboard } from "@/lib/data";

export default async function DashboardPage() {
  const dashboard = await getCoverageDashboard();

  return (
    <main className="mx-auto max-w-5xl p-8">
      <h1 className="text-3xl font-semibold">Coverage dashboard</h1>
      <p className="mt-2 text-gray-600">
        Aggregate claim and formalization coverage from corpus manifests.
      </p>
      <p className="mt-2 text-sm text-gray-500">
        Extraction and proof metrics: see the benchmark report (
        <code className="rounded bg-gray-100 px-1">
          benchmarks/reports/latest.json
        </code>
        ) or run{" "}
        <code className="rounded bg-gray-100 px-1">just benchmark</code>. For
        the full map of SPEC metrics to sources, see{" "}
        <code className="rounded bg-gray-100 px-1">docs/metrics.md</code> in the
        repository.
      </p>

      <section className="mt-8">
        <h2 className="text-xl font-medium">Milestone 3 (content target)</h2>
        <p className="mt-1 text-sm text-gray-600">
          Target: 20–40 meaningful claims machine-checked. Close by adding and
          formalizing more claims.
        </p>
        <p className="mt-1 text-sm">
          <a
            href="https://github.com/fraware/scientific-memory/blob/main/ROADMAP.md#content-sprint-checklist-reach-20-40-claims"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline"
          >
            How to contribute content
          </a>{" "}
          (Content sprint checklist, CONTRIBUTING.md)
        </p>
        <div className="mt-2 flex items-baseline gap-2">
          <span className="text-2xl font-semibold">
            {dashboard.totalMachineChecked}
          </span>
          <span className="text-gray-500">/ 40 machine-checked</span>
        </div>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-medium">Totals</h2>
        <div className="mt-2 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="rounded border bg-gray-50 p-3">
            <div className="text-2xl font-semibold">
              {dashboard.totalClaims}
            </div>
            <div className="text-xs text-gray-600">Claims</div>
          </div>
          <div className="rounded border bg-gray-50 p-3">
            <div className="text-2xl font-semibold">
              {dashboard.totalMapped}
            </div>
            <div className="text-xs text-gray-600">Mapped</div>
          </div>
          <div className="rounded border bg-gray-50 p-3">
            <div className="text-2xl font-semibold">
              {dashboard.totalMachineChecked}
            </div>
            <div className="text-xs text-gray-600">Machine-checked</div>
          </div>
          <div className="rounded border bg-gray-50 p-3">
            <div className="text-2xl font-semibold">
              {dashboard.totalKernelLinked}
            </div>
            <div className="text-xs text-gray-600">Kernel-linked</div>
          </div>
        </div>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-medium">Reviewer Status (Theorem Cards)</h2>
        <div className="mt-2 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="rounded border bg-red-50 p-3">
            <div className="text-2xl font-semibold text-red-700">
              {dashboard.totalReviewerBlocked}
            </div>
            <div className="text-xs text-gray-700">Blocked</div>
          </div>
          <div className="rounded border bg-amber-50 p-3">
            <div className="text-2xl font-semibold text-amber-700">
              {dashboard.totalReviewerUnreviewed}
            </div>
            <div className="text-xs text-gray-700">Unreviewed</div>
          </div>
          <div className="rounded border bg-blue-50 p-3">
            <div className="text-2xl font-semibold text-blue-700">
              {dashboard.totalReviewerReviewed}
            </div>
            <div className="text-xs text-gray-700">Reviewed</div>
          </div>
          <div className="rounded border bg-green-50 p-3">
            <div className="text-2xl font-semibold text-green-700">
              {dashboard.totalReviewerAccepted}
            </div>
            <div className="text-xs text-gray-700">Accepted</div>
          </div>
        </div>
      </section>

      <section className="mt-8">
        <h2 className="text-xl font-medium">By paper</h2>
        <ul className="mt-3 space-y-3">
          {dashboard.papers.map((p) => (
            <li key={p.paperId} className="rounded border p-4">
              <Link
                href={`/papers/${p.paperId}`}
                className="font-medium text-blue-600 hover:underline"
              >
                {p.title}
              </Link>
              <span className="ml-2 text-sm text-gray-500">{p.paperId}</span>
              <div className="mt-2 flex gap-4 text-sm">
                <span>{p.claimCount} claims</span>
                <span>{p.mappedCount} mapped</span>
                <span>{p.machineCheckedCount} machine-checked</span>
                <span>{p.kernelLinkedCount} kernel-linked</span>
              </div>
              <div className="mt-1 flex gap-3 text-xs text-gray-600">
                <span>blocked {p.reviewerBlockedCount}</span>
                <span>unreviewed {p.reviewerUnreviewedCount}</span>
                <span>reviewed {p.reviewerReviewedCount}</span>
                <span>accepted {p.reviewerAcceptedCount}</span>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
