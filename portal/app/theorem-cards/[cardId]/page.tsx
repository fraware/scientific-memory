import Link from "next/link";
import { getTheoremCardById, getAllTheoremCardIds } from "@/lib/data";
import { DependencyGraph } from "@/components/DependencyGraph";

export async function generateStaticParams() {
  const ids = await getAllTheoremCardIds();
  return ids.map((cardId) => ({ cardId }));
}

export const dynamicParams = false;

export default async function TheoremCardPage({
  params,
}: {
  params: Promise<{ cardId: string }>;
}) {
  const { cardId } = await params;
  const data = await getTheoremCardById(cardId);

  if (!data) {
    return (
      <main className="mx-auto max-w-5xl p-8">
        <h1 className="text-3xl font-semibold">Theorem card not found</h1>
        <p className="mt-2 text-gray-600">
          No theorem card “{cardId}” in corpus.
        </p>
      </main>
    );
  }

  const {
    paperId,
    claimId,
    claim,
    declaration,
    namespace,
    metadata,
    manifest,
    verificationBoundary,
    linkedKernelIds,
    filePath,
    reviewerStatus,
    notes,
  } = data;
  const dependencyGraph =
    (manifest.dependency_graph as { from: string; to: string }[]) ?? [];
  const graphEdges = dependencyGraph.filter(
    (e) => e.from === declaration || e.to === declaration,
  );

  return (
    <main className="mx-auto max-w-5xl p-8">
      <h1 className="text-3xl font-semibold font-mono">{declaration}</h1>
      <p className="mt-2 text-sm text-gray-600">
        Paper:{" "}
        <Link
          href={`/papers/${paperId}`}
          className="text-blue-600 hover:underline"
        >
          {metadata.title as string}
        </Link>
        {" · "}
        Claim:{" "}
        <Link
          href={`/claims/${claimId}`}
          className="text-blue-600 hover:underline"
        >
          {claimId}
        </Link>
      </p>

      <section className="mt-6">
        <h2 className="text-lg font-medium">Proof status</h2>
        <p className="mt-2">
          <span className="rounded bg-gray-200 px-2 py-1 text-sm">
            {String(claim.status)}
          </span>
        </p>
      </section>

      {verificationBoundary && (
        <section className="mt-6">
          <h2 className="text-lg font-medium">Verification boundary</h2>
          <p className="mt-2">
            <span className="rounded bg-gray-200 px-2 py-1 text-sm">
              {verificationBoundary}
            </span>
          </p>
        </section>
      )}

      {linkedKernelIds.length > 0 && (
        <section className="mt-6">
          <h2 className="text-lg font-medium">Linked kernels</h2>
          <ul className="mt-2 space-y-2">
            {linkedKernelIds.map((kid) => (
              <li key={kid}>
                <Link
                  href={`/kernels/${encodeURIComponent(kid)}`}
                  className="text-blue-600 hover:underline"
                >
                  {kid}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {filePath && (
        <section className="mt-6">
          <h2 className="text-lg font-medium">File path</h2>
          <p className="mt-2 font-mono text-sm">{filePath}</p>
        </section>
      )}

      {reviewerStatus && (
        <section className="mt-6">
          <h2 className="text-lg font-medium">Reviewer status</h2>
          <p className="mt-2">
            <span className="rounded bg-gray-200 px-2 py-1 text-sm">
              {reviewerStatus}
            </span>
          </p>
        </section>
      )}

      {notes && (
        <section className="mt-6">
          <h2 className="text-lg font-medium">Notes</h2>
          <p className="mt-2 text-sm text-gray-700">{notes}</p>
        </section>
      )}

      <section className="mt-6">
        <h2 className="text-lg font-medium">Linked claim</h2>
        <p className="mt-2 text-sm text-gray-700">
          {String(claim.informal_text ?? "")}
        </p>
      </section>

      {graphEdges.length > 0 && (
        <section className="mt-6">
          <h2 className="text-lg font-medium">Dependency graph</h2>
          <p className="mt-1 text-sm text-gray-600">
            Edges involving this declaration. Click a node to open its theorem
            card.
          </p>
          <div className="mt-2">
            <DependencyGraph
              edges={graphEdges}
              highlightNode={declaration}
              nodeHrefById={Object.fromEntries(
                Array.from(
                  new Set(graphEdges.flatMap((e) => [e.from, e.to])),
                ).map((id) => [id, `/theorem-cards/${encodeURIComponent(id)}`]),
              )}
            />
          </div>
        </section>
      )}

      <section className="mt-6">
        <h2 className="text-lg font-medium">Namespace</h2>
        <p className="mt-2 font-mono text-sm">{namespace}</p>
      </section>
    </main>
  );
}
