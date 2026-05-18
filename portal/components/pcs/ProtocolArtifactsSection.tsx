import type { PcsProtocolArtifact } from "@/lib/pcsTypes";

import { ProtocolArtifactView } from "./ProtocolArtifactView";

interface ProtocolArtifactsSectionProps {
  artifacts: PcsProtocolArtifact[];
}

export function ProtocolArtifactsSection({ artifacts }: ProtocolArtifactsSectionProps) {
  if (!artifacts.length) return null;
  return (
    <section data-testid="pcs-section-protocol-artifacts">
      <h2 className="text-lg font-medium">Protocol artifacts</h2>
      <div className="mt-4 space-y-4">
        {artifacts.map((artifact) => (
          <ProtocolArtifactView key={`${artifact.artifact_type}-${artifact.name}`} artifact={artifact} />
        ))}
      </div>
    </section>
  );
}
