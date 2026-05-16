import Link from "next/link";

import { getAllPcsClaimIds, getPcsClaimById } from "@/lib/pcsData";

export default async function PcsClaimsIndexPage() {
  const claimIds = await getAllPcsClaimIds();

  return (
    <main className="mx-auto max-w-5xl p-8">
      <h1 className="text-3xl font-semibold">PCS claims</h1>
      <p className="mt-2 text-gray-600">
        Proof-carrying science artifacts imported from signed LabTrust bundles.
      </p>

      {claimIds.length === 0 ? (
        <p className="mt-6 text-sm text-gray-600">
          No claims imported yet. Run{" "}
          <code className="rounded bg-gray-100 px-1">just pcs-import-bundle</code>{" "}
          then{" "}
          <code className="rounded bg-gray-100 px-1">just pcs-render-claim</code>.
        </p>
      ) : (
        <ul className="mt-6 space-y-3">
          {await Promise.all(
            claimIds.map(async (claimId) => {
              const model = await getPcsClaimById(claimId);
              return (
                <li key={claimId} className="rounded border p-4">
                  <Link
                    href={`/pcs/claims/${claimId}`}
                    className="font-medium text-blue-600 hover:underline"
                  >
                    {claimId}
                  </Link>
                  {model?.claim?.text != null && (
                    <p className="mt-2 line-clamp-2 text-sm text-gray-700">
                      {model.claim.text}
                    </p>
                  )}
                  {model?.claim?.status != null && (
                    <p className="mt-1 text-xs text-gray-500">
                      Status: {model.claim.status}
                    </p>
                  )}
                </li>
              );
            }),
          )}
        </ul>
      )}
    </main>
  );
}
