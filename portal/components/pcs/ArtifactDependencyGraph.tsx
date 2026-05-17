import type { PcsArtifactDependencyEdge } from "@/lib/pcsTypes";

interface Props {
  edges: PcsArtifactDependencyEdge[];
}

export function ArtifactDependencyGraph({ edges }: Props) {
  if (!edges.length) {
    return null;
  }
  return (
    <section data-testid="pcs-section-artifact-dependency-graph">
      <h2 className="text-xl font-semibold">Artifact Dependency Graph</h2>
      <ul className="mt-3 space-y-1 font-mono text-xs">
        {edges.map((edge) => (
          <li key={`${edge.from}-${edge.to}`}>
            {edge.from} → {edge.to}
            {edge.kind ? <span className="text-gray-500"> ({edge.kind})</span> : null}
          </li>
        ))}
      </ul>
    </section>
  );
}
