import Link from "next/link";
import { getPaperBundle, getPapersList } from "@/lib/data";
import { DependencyGraph } from "@/components/DependencyGraph";

export async function generateStaticParams() {
  const papers = await getPapersList();
  return papers.map((p) => ({ paperId: p.id }));
}

export const dynamicParams = false;

export default async function PaperPage({
  params,
}: {
  params: Promise<{ paperId: string }>;
}) {
  const { paperId } = await params;
  const bundle = await getPaperBundle(paperId);
  const coverage =
    (bundle.manifest.coverage_metrics as Record<string, unknown>) ?? {};
  const declarationIndex =
    (bundle.manifest.declaration_index as string[]) ?? [];
  const kernelIndex = (bundle.manifest.kernel_index as string[]) ?? [];
  const dependencyGraph =
    (bundle.manifest.dependency_graph as { from: string; to: string }[]) ?? [];
  const claims = bundle.claims as Record<string, unknown>[];
  const disputed = claims.filter((c) => String(c.status) === "disputed");
  const assumptions = bundle.assumptions as Record<string, unknown>[];

  return (
    <main className="mx-auto max-w-5xl p-8">
      <h1 className="text-3xl font-semibold">
        {(bundle.metadata.title as string) ?? paperId}
      </h1>
      <p className="mt-2 text-sm text-gray-600">
        {(bundle.metadata.authors as string[])?.join(", ")} ·{" "}
        {bundle.metadata.year as number}
      </p>
      {bundle.manifest.version != null &&
      String(bundle.manifest.version).length > 0 ? (
        <p className="mt-1 text-xs text-gray-500">
          Version {String(bundle.manifest.version)}
        </p>
      ) : null}

      <section className="mt-8">
        <h2 className="text-xl font-medium">Coverage</h2>
        <div className="mt-2 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="rounded border bg-gray-50 p-3">
            <div className="text-2xl font-semibold">
              {Number(coverage.claim_count) || 0}
            </div>
            <div className="text-xs text-gray-600">Claims</div>
          </div>
          <div className="rounded border bg-gray-50 p-3">
            <div className="text-2xl font-semibold">
              {declarationIndex.length}
            </div>
            <div className="text-xs text-gray-600">Declarations</div>
          </div>
          <div className="rounded border bg-gray-50 p-3">
            <div className="text-2xl font-semibold">{kernelIndex.length}</div>
            <div className="text-xs text-gray-600">Kernels</div>
          </div>
          <div className="rounded border bg-gray-50 p-3">
            <div className="text-2xl font-semibold">
              {Number(coverage.machine_checked_count) || 0}
            </div>
            <div className="text-xs text-gray-600">Machine-checked</div>
          </div>
        </div>
      </section>

      {assumptions.length > 0 && (
        <section className="mt-8">
          <h2 className="text-xl font-medium">Assumptions</h2>
          <ul className="mt-3 space-y-2">
            {assumptions.map((a: Record<string, unknown>) => (
              <li key={String(a.id)} className="rounded border p-3 text-sm">
                <span className="font-medium">{String(a.id)}</span>
                <span className="text-gray-600"> · {String(a.kind)}</span>
                <p className="mt-1 text-gray-700">{String(a.text ?? "")}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      {dependencyGraph.length > 0 && (
        <section className="mt-8">
          <h2 className="text-xl font-medium">Dependency graph</h2>
          <p className="mt-1 text-sm text-gray-600">
            Declaration dependencies from manifest. Click a node to open its
            theorem card.
          </p>
          <div className="mt-2">
            <DependencyGraph
              edges={dependencyGraph}
              nodeHrefById={Object.fromEntries(
                Array.from(
                  new Set(dependencyGraph.flatMap((e) => [e.from, e.to])),
                ).map((id) => [id, `/theorem-cards/${encodeURIComponent(id)}`]),
              )}
            />
          </div>
        </section>
      )}

      {disputed.length > 0 && (
        <section className="mt-8">
          <h2 className="text-xl font-medium text-amber-700">
            Disputed claims
          </h2>
          <ul className="mt-3 space-y-2">
            {disputed.map((c: Record<string, unknown>) => (
              <li
                key={String(c.id)}
                className="rounded border border-amber-200 bg-amber-50 p-3"
              >
                <Link
                  href={`/claims/${encodeURIComponent(String(c.id))}`}
                  className="font-medium text-blue-600 hover:underline"
                >
                  {String(c.id)}
                </Link>
                {" · "}
                {String(c.informal_text ?? "").slice(0, 80)}…
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="mt-8">
        <h2 className="text-xl font-medium">Claims</h2>
        <ul className="mt-3 space-y-3">
          {claims.map((claim: Record<string, unknown>) => (
            <li key={String(claim.id)} className="rounded border p-4">
              <Link
                href={`/claims/${claim.id}`}
                className="font-medium text-blue-600 hover:underline"
              >
                {String(claim.id)}
              </Link>
              <div className="text-sm text-gray-700 mt-1">
                {String(claim.informal_text ?? "")}
              </div>
              <div className="mt-2 text-xs text-gray-500">
                {String(claim.claim_type)} · {String(claim.status)}
              </div>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
