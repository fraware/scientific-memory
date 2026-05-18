import type { PcsNamedArtifact } from "@/lib/pcsTypes";

import { NamedProtocolArtifactView } from "./NamedProtocolArtifactView";

interface ToolUseCertificateViewProps {
  certificate: PcsNamedArtifact;
}

export function ToolUseCertificateView({ certificate }: ToolUseCertificateViewProps) {
  return (
    <NamedProtocolArtifactView
      title="Tool-Use Certificate"
      testId="pcs-section-tool-use-certificate"
      artifact={certificate}
    />
  );
}
