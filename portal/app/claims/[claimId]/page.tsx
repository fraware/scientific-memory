import Link from "next/link";
import { getClaimById, getAllClaimIds } from "@/lib/data";

export async function generateStaticParams() {
  const ids = await getAllClaimIds();
  return ids.map((claimId) => ({ claimId }));
}

export const dynamicParams = false;

export default async function ClaimPage({
  params,
}: {
  params: Promise<{ claimId: string }>;
}) {
  const { claimId } = await params;
  const data = await getClaimById(claimId);

  if (!data) {
    return (
      <main className="mx-auto max-w-5xl p-8">
        <h1 className="text-3xl font-semibold">Claim not found</h1>
        <p className="mt-2 text-gray-600">
          No claim with id “{claimId}” in corpus.
        </p>
      </main>
    );
  }

  const { claim, paperId, metadata, assumptions, symbols, mapping } = data;
  const sourceSpan = claim.source_span as Record<string, unknown> | undefined;
  const linkedAssumptionIds = (claim.linked_assumptions as string[]) ?? [];
  const linkedAssumptions = assumptions.filter((a) =>
    linkedAssumptionIds.includes(String(a.id)),
  );
  const linkedSymbolIds = (claim.linked_symbols as string[]) ?? [];
  const linkedSymbols = symbols.filter((s) =>
    linkedSymbolIds.includes(String(s.id)),
  );
  const claimToDecl = (mapping.claim_to_decl as Record<string, string>) ?? {};
  const formalDecl = claimToDecl[claimId];

  return (
    <main className="mx-auto max-w-5xl p-8">
      <h1 className="text-3xl font-semibold">{String(claim.id)}</h1>
      <p className="mt-2 text-sm text-gray-600">
        Paper:{" "}
        <Link
          href={`/papers/${paperId}`}
          className="text-blue-600 hover:underline"
        >
          {metadata.title as string}
        </Link>
      </p>

      <section className="mt-6">
        <h2 className="text-lg font-medium">Source text</h2>
        <p className="mt-2 rounded border bg-gray-50 p-4 text-sm">
          {String(claim.informal_text ?? "")}
        </p>
      </section>

      {sourceSpan && (
        <section className="mt-6">
          <h2 className="text-lg font-medium">Source span</h2>
          <pre className="mt-2 rounded border bg-gray-50 p-3 text-xs">
            {JSON.stringify(sourceSpan, null, 2)}
          </pre>
        </section>
      )}

      <section className="mt-6">
        <h2 className="text-lg font-medium">Status</h2>
        <p className="mt-2">
          <span className="rounded bg-gray-200 px-2 py-1 text-sm">
            {String(claim.claim_type)}
          </span>
          <span className="ml-2 rounded bg-gray-200 px-2 py-1 text-sm">
            {String(claim.status)}
          </span>
        </p>
      </section>

      {linkedAssumptions.length > 0 && (
        <section className="mt-6">
          <h2 className="text-lg font-medium">Linked assumptions</h2>
          <ul className="mt-2 space-y-2">
            {linkedAssumptions.map((a: Record<string, unknown>) => (
              <li key={String(a.id)} className="rounded border p-3 text-sm">
                <span className="font-medium">{String(a.id)}</span>
                <span className="text-gray-600"> · {String(a.kind)}</span>
                <p className="mt-1 text-gray-700">{String(a.text ?? "")}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      {linkedSymbols.length > 0 && (
        <section className="mt-6">
          <h2 className="text-lg font-medium">Normalized symbols</h2>
          <ul className="mt-2 space-y-2">
            {linkedSymbols.map((s: Record<string, unknown>) => (
              <li key={String(s.id)} className="rounded border p-3 text-sm">
                <span className="font-medium">{String(s.id)}</span>
                {s.raw_latex != null && (
                  <span className="text-gray-600">
                    {" "}
                    · LaTeX: {String(s.raw_latex)}
                  </span>
                )}
                {s.normalized_name != null && (
                  <span className="text-gray-600">
                    {" "}
                    · normalized: {String(s.normalized_name)}
                  </span>
                )}
                {s.type_hint != null && (
                  <span className="text-gray-600">
                    {" "}
                    · type: {String(s.type_hint)}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      {formalDecl && (
        <section className="mt-6">
          <h2 className="text-lg font-medium">Formal target</h2>
          <p className="mt-2 font-mono text-sm">
            {String(mapping.namespace)}.{formalDecl}
          </p>
        </section>
      )}

      {(claim.review_notes as string) && (
        <section className="mt-6">
          <h2 className="text-lg font-medium">Review notes</h2>
          <p className="mt-2 text-sm text-gray-700">
            {String(claim.review_notes)}
          </p>
        </section>
      )}
    </main>
  );
}
