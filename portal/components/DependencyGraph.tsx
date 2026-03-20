"use client";

import { useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  ReactFlow,
  type Node,
  type Edge,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

export type DependencyGraphEdge = { from: string; to: string };

function buildLayout(
  edges: DependencyGraphEdge[],
): Map<string, { x: number; y: number }> {
  const nodeIds = new Set<string>();
  for (const e of edges) {
    nodeIds.add(e.from);
    nodeIds.add(e.to);
  }
  const order = Array.from(nodeIds);
  const position = new Map<string, { x: number; y: number }>();
  const colWidth = 220;
  const rowHeight = 70;
  order.forEach((id, i) => {
    position.set(id, {
      x: (i % 3) * colWidth,
      y: Math.floor(i / 3) * rowHeight,
    });
  });
  return position;
}

type Props = {
  edges: DependencyGraphEdge[];
  highlightNode?: string;
  /** Per-node link targets (JSON-serializable for RSC). Omit or empty to disable navigation. */
  nodeHrefById?: Record<string, string>;
};

export function DependencyGraph({ edges, highlightNode, nodeHrefById }: Props) {
  const router = useRouter();
  const positionMap = useMemo(() => buildLayout(edges), [edges]);
  const clickable = Boolean(
    nodeHrefById && Object.keys(nodeHrefById).length > 0,
  );

  const initialNodes: Node[] = useMemo(() => {
    return Array.from(positionMap.entries()).map(([id, pos]) => ({
      id,
      type: "default",
      position: pos,
      data: { label: id.length > 40 ? id.slice(0, 37) + "…" : id },
      className:
        highlightNode && id === highlightNode ? "ring-2 ring-blue-500" : "",
    }));
  }, [positionMap, highlightNode]);

  const initialEdges: Edge[] = useMemo(() => {
    return edges.map((e, i) => ({
      id: `e-${i}-${e.from}-${e.to}`,
      source: e.from,
      target: e.to,
    }));
  }, [edges]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edgesState, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      const href = nodeHrefById?.[node.id];
      if (href) router.push(href);
    },
    [nodeHrefById, router],
  );

  if (edges.length === 0) return null;

  return (
    <div
      className={`h-[320px] w-full rounded border bg-white ${clickable ? "[&_.react-flow__node]:cursor-pointer" : ""}`}
    >
      <ReactFlow
        nodes={nodes}
        edges={edgesState}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.2}
        maxZoom={1.5}
      >
        <Background />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
