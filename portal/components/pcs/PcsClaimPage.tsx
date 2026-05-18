import type { PcsClaimReadModel } from "@/lib/pcsTypes";

import { ArtifactDependencyGraph } from "./ArtifactDependencyGraph";
import { ArtifactHashTable } from "./ArtifactHashTable";
import { ArtifactRegistryView } from "./ArtifactRegistryView";
import { AssumptionSetView } from "./AssumptionSetView";
import { ClaimArtifactView } from "./ClaimArtifactView";
import { EvidenceBundleView } from "./EvidenceBundleView";
import { LimitationNotice } from "./LimitationNotice";
import { LineageView } from "./LineageView";
import { ReleaseChainValidationView } from "./ReleaseChainValidationView";
import { ReleaseManifestView } from "./ReleaseManifestView";
import { StalenessView } from "./StalenessView";
import { ReplayCommand } from "./ReplayCommand";
import { RuntimeReceiptView } from "./RuntimeReceiptView";
import { SourceRepositories } from "./SourceRepositories";
import { TraceCertificateView } from "./TraceCertificateView";
import { VerificationResultView } from "./VerificationResultView";

interface PcsClaimPageProps {
  model: PcsClaimReadModel;
}

export function PcsClaimPage({ model }: PcsClaimPageProps) {
  const extraLimitations = model.limitations.filter(
    (l) => l !== model.limitation_notice,
  );
  return (
    <main className="mx-auto max-w-5xl space-y-8 p-8" data-testid="pcs-claim-page">
      <header>
        <p className="text-sm text-gray-500">LabTrust PCS claim</p>
        <h1 className="text-3xl font-semibold">{model.claim_id}</h1>
        <p className="mt-1 font-mono text-xs text-gray-500">
          Bundle digest: {model.bundle_signature_or_digest}
        </p>
      </header>

      <ClaimArtifactView claim={model.claim} />
      <AssumptionSetView assumptionSet={model.assumption_set} />
      <RuntimeReceiptView receipt={model.runtime_receipt} />
      <TraceCertificateView certificate={model.trace_certificate} />
      {model.evidence_bundle?.id ? (
        <EvidenceBundleView evidence={model.evidence_bundle} />
      ) : null}
      <VerificationResultView result={model.verification_result} />
      {model.release_manifest ? (
        <ReleaseManifestView manifest={model.release_manifest} />
      ) : null}
      {model.release_chain_validation ? (
        <ReleaseChainValidationView validation={model.release_chain_validation} />
      ) : null}
      {model.artifact_registry?.length ? (
        <ArtifactRegistryView entries={model.artifact_registry} />
      ) : null}
      {model.artifact_dependency_graph?.length ? (
        <ArtifactDependencyGraph edges={model.artifact_dependency_graph} />
      ) : null}
      {model.lineage ? <LineageView lineage={model.lineage} /> : null}
      {model.staleness ? <StalenessView staleness={model.staleness} /> : null}
      <ArtifactHashTable
        hashes={model.artifact_hashes}
        canonicalDigests={model.canonical_digests}
      />
      <SourceRepositories sources={model.source_repositories} />
      <ReplayCommand
        reproduceCommands={model.reproduce_commands}
        verifyCommands={model.verify_commands}
      />
      <LimitationNotice notice={model.limitation_notice} additional={extraLimitations} />
    </main>
  );
}
