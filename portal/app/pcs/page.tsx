import Link from "next/link";

import { getAllPcsClaimIds, getPcsClaimById } from "@/lib/pcsData";

export default async function PcsClaimsIndexPage() {
  const claimIds = await getAllPcsClaimIds();

  return (
    <main className="mx-auto max-w-5xl p-8">
      <h1 className="text-3xl font-semibold">PCS claims</h1>
      <p className="mt-2 text-gray-600">
        Proof-carrying science releases imported from{" "}
        <code className="rounded bg-gray-100 px-1">ReleaseManifest.v0</code>.
      </p>

      {claimIds.length === 0 ? (
        <p className="mt-6 text-sm text-gray-600">
          No claims imported yet. Run{" "}
          <code className="rounded bg-gray-100 px-1">just pcs-import-release</code>{" "}
          then{" "}
          <code className="rounded bg-gray-100 px-1">just pcs-render-claim claim-pcs-qc-release-v0.1</code>.
        </p>
      ) : (
        <ul className="mt-6 space-y-3">
          {await Promise.all(
            claimIds.map(async (claimId) => {
              const model = await getPcsClaimById(claimId);
              const releaseId = model?.release_manifest?.release_id;
              const stale = model?.staleness?.stale === true;
              return (
                <li key={claimId} className="rounded border p-4">
                  <ClaimListHeader claimId={claimId} releaseId={releaseId} stale={stale} />
                  {model?.claim?.text != null && (
                    <p className="mt-2 line-clamp-2 text-sm text-gray-700">
                      {model.claim.text}
                    </p>
                  )}
                  {model?.claim?.status != null && (
                    <p className="mt-1 text-xs text-gray-500">
                      Claim status: {model.claim.status}
                      {model?.release_chain_validation?.status != null
                        ? ` · Chain: ${model.release_chain_validation.status}`
                        : ""}
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

function ClaimListHeader({
  claimId,
  releaseId,
  stale,
}: {
  claimId: string;
  releaseId?: string;
  stale: boolean;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Link
        href={`/pcs/claims/${claimId}`}
        className="font-medium text-blue-600 hover:underline"
      >
        {claimId}
      </Link>
      {releaseId ? (
        <span className="rounded bg-gray-100 px-2 py-0.5 font-mono text-xs text-gray-600">
          {releaseId}
        </span>
      ) : null}
      {stale ? (
        <span className="rounded bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
          Stale
        </span>
      ) : (
        <span className="rounded bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
          Fresh
        </span>
      )}
    </div>
  );
}
