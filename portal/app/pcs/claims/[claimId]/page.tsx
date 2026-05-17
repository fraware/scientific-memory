import { PcsClaimPage } from "@/components/pcs/PcsClaimPage";
import { getAllPcsClaimIds, getPcsClaimById } from "@/lib/pcsData";

export async function generateStaticParams() {
  const ids = await getAllPcsClaimIds();
  return ids.map((claimId) => ({ claimId }));
}

export const dynamicParams = process.env.NODE_ENV === "development";

export default async function PcsClaimRoute({
  params,
}: {
  params: Promise<{ claimId: string }>;
}) {
  const { claimId } = await params;
  const model = await getPcsClaimById(claimId);

  if (!model) {
    return (
      <main className="mx-auto max-w-5xl p-8">
        <h1 className="text-3xl font-semibold">PCS claim not found</h1>
        <p className="mt-2 text-gray-600">
          No imported claim with id “{claimId}”. Run{" "}
          <code className="rounded bg-gray-100 px-1">just pcs-import-bundle</code>{" "}
          then{" "}
          <code className="rounded bg-gray-100 px-1">just pcs-render-claim</code>.
        </p>
      </main>
    );
  }

  return <PcsClaimPage model={model} />;
}
