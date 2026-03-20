import Link from "next/link";
import { getKernelById, getAllKernelIds } from "@/lib/data";

export async function generateStaticParams() {
  const ids = await getAllKernelIds();
  return ids.map((kernelId) => ({ kernelId }));
}

export const dynamicParams = false;

export default async function KernelPage({
  params,
}: {
  params: Promise<{ kernelId: string }>;
}) {
  const { kernelId } = await params;
  const data = await getKernelById(kernelId);

  if (!data) {
    return (
      <main className="mx-auto max-w-5xl p-8">
        <h1 className="text-3xl font-semibold">Kernel not found</h1>
        <p className="mt-2 text-gray-600">No kernel “{kernelId}” in corpus.</p>
      </main>
    );
  }

  const { kernel, paperIds } = data;
  const linkedCards = (kernel.linked_theorem_cards as string[]) ?? [];
  const unitConstraints =
    (kernel.unit_constraints as string[] | undefined) ?? [];
  const domain = String(kernel.domain ?? "");
  const inputSchema = String(kernel.input_schema ?? "");
  const outputSchema = String(kernel.output_schema ?? "");
  const semanticContract = String(kernel.semantic_contract ?? "");
  const testStatus = String(kernel.test_status ?? "");

  return (
    <main className="mx-auto max-w-5xl p-8">
      <h1 className="text-3xl font-semibold">{String(kernel.id)}</h1>
      {domain && <p className="mt-2 text-sm text-gray-600">Domain: {domain}</p>}

      {semanticContract && (
        <section className="mt-6">
          <h2 className="text-lg font-medium">Semantic contract</h2>
          <p className="mt-2 rounded border bg-gray-50 p-4 text-sm">
            {semanticContract}
          </p>
        </section>
      )}

      {(inputSchema || outputSchema) && (
        <section className="mt-6">
          <h2 className="text-lg font-medium">Input / output</h2>
          <div className="mt-2 space-y-2 rounded border bg-gray-50 p-4 font-mono text-sm">
            {inputSchema && <div>Input: {inputSchema}</div>}
            {outputSchema && <div>Output: {outputSchema}</div>}
          </div>
        </section>
      )}

      {unitConstraints.length > 0 && (
        <section className="mt-6">
          <h2 className="text-lg font-medium">Unit constraints</h2>
          <ul className="mt-2 list-inside list-disc space-y-1 rounded border bg-gray-50 p-4 text-sm">
            {unitConstraints.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </section>
      )}

      {linkedCards.length > 0 && (
        <section className="mt-6">
          <h2 className="text-lg font-medium">Linked theorem cards</h2>
          <ul className="mt-2 space-y-2">
            {linkedCards.map((cardId) => (
              <li key={cardId}>
                <Link
                  href={`/theorem-cards/${cardId}`}
                  className="text-blue-600 hover:underline"
                >
                  {cardId}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {paperIds.length > 0 && (
        <section className="mt-6">
          <h2 className="text-lg font-medium">Papers</h2>
          <ul className="mt-2 space-y-2">
            {paperIds.map((pid) => (
              <li key={pid}>
                <Link
                  href={`/papers/${pid}`}
                  className="text-blue-600 hover:underline"
                >
                  {pid}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {testStatus && (
        <section className="mt-6">
          <h2 className="text-lg font-medium">Test status</h2>
          <p className="mt-2">
            <span className="rounded bg-gray-200 px-2 py-1 text-sm">
              {testStatus}
            </span>
          </p>
        </section>
      )}

      <section className="mt-6">
        <h2 className="text-lg font-medium">
          Reproducible runs / Example outputs
        </h2>
        <p className="mt-2 text-sm text-gray-600">
          Example run for this kernel. To reproduce locally, run the kernel
          package tests from the repo root.
        </p>
        {String(kernel.id) === "langmuir_adsorption_kernel_v1" && (
          <div className="mt-3 space-y-2 rounded border bg-gray-50 p-4 font-mono text-sm">
            <div>Input: K = 1, P = 0.5</div>
            <div>
              Output: coverage ≈ 0.333 (Langmuir isotherm K*P / (1 + K*P))
            </div>
            <p className="mt-2 text-xs text-gray-500 not-italic">
              Package: kernels/adsorption. Run: uv run --project
              kernels/adsorption pytest
            </p>
          </div>
        )}
        {String(kernel.id) !== "langmuir_adsorption_kernel_v1" && (
          <p className="mt-2 text-sm text-gray-500">
            No example run documented for this kernel yet.
          </p>
        )}
      </section>
    </main>
  );
}
