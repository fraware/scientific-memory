import type { PcsNamedArtifact } from "@/lib/pcsTypes";

import { NamedProtocolArtifactView } from "./NamedProtocolArtifactView";

interface ToolUseTraceViewProps {
  trace: PcsNamedArtifact;
}

export function ToolUseTraceView({ trace }: ToolUseTraceViewProps) {
  return (
    <NamedProtocolArtifactView
      title="Tool-Use Trace"
      testId="pcs-section-tool-use-trace"
      artifact={trace}
    />
  );
}
