"""Dependency reuse ratio and theorem-card fan-in / fan-out (SPEC 12)."""

import json
from pathlib import Path


def compute_dependency_metrics(repo_root: Path) -> dict:
    """
    Read all papers' dependency_graph (from manifest or theorem_cards);
    compute reuse ratio, per-declaration fan-in/fan-out, and aggregates.
    Purely derived; no schema change.
    """
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    index_path = repo_root / "corpus" / "index.json"
    if not papers_dir.is_dir() or not index_path.exists():
        return _empty_metrics()
    index = json.loads(index_path.read_text(encoding="utf-8"))
    paper_list = index.get("papers") or []
    paper_ids = [p["id"] for p in paper_list if isinstance(p, dict) and p.get("id")]

    edges: list[tuple[str, str]] = []
    all_to_nodes: list[str] = []

    for paper_id in paper_ids:
        paper_dir = papers_dir / paper_id
        manifest_path = paper_dir / "manifest.json"
        graph_loaded = False
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
            else:
                graph = manifest.get("dependency_graph") or []
                if isinstance(graph, list) and graph:
                    for e in graph:
                        if isinstance(e, dict) and e.get("from") and e.get("to"):
                            edges.append((str(e["from"]), str(e["to"])))
                            all_to_nodes.append(str(e["to"]))
                    graph_loaded = True
        if not graph_loaded:
            cards_path = paper_dir / "theorem_cards.json"
            if cards_path.exists():
                try:
                    cards = json.loads(cards_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    cards = None
                if isinstance(cards, list):
                    for c in cards:
                        if not isinstance(c, dict):
                            continue
                        lean_decl = c.get("lean_decl")
                        dep_ids = c.get("dependency_ids") or []
                        if lean_decl and isinstance(dep_ids, list):
                            for d in dep_ids:
                                if d:
                                    edges.append((str(d), str(lean_decl)))
                                    all_to_nodes.append(str(lean_decl))

    if not edges:
        return _empty_metrics()

    to_counts: dict[str, int] = {}
    for _, to_node in edges:
        to_counts[to_node] = to_counts.get(to_node, 0) + 1
    shared_targets = sum(1 for c in to_counts.values() if c > 1)
    total_edges = len(edges)
    reuse_ratio = sum(c for c in to_counts.values() if c > 1) / total_edges if total_edges else 0.0

    in_degree: dict[str, int] = {}
    out_degree: dict[str, int] = {}
    for from_n, to_n in edges:
        in_degree[to_n] = in_degree.get(to_n, 0) + 1
        out_degree[from_n] = out_degree.get(from_n, 0) + 1
    all_nodes = set(in_degree) | set(out_degree)
    in_vals = [in_degree.get(n, 0) for n in all_nodes]
    out_vals = [out_degree.get(n, 0) for n in all_nodes]
    avg_fan_in = sum(in_vals) / len(in_vals) if in_vals else 0.0
    avg_fan_out = sum(out_vals) / len(out_vals) if out_vals else 0.0
    max_fan_in = max(in_vals) if in_vals else 0
    max_fan_out = max(out_vals) if out_vals else 0

    return {
        "dependency_reuse_ratio": round(reuse_ratio, 4),
        "total_edges": total_edges,
        "declarations_with_in_degree": len([v for v in in_vals if v > 0]),
        "average_fan_in": round(avg_fan_in, 4),
        "average_fan_out": round(avg_fan_out, 4),
        "max_fan_in": max_fan_in,
        "max_fan_out": max_fan_out,
        "shared_targets_count": shared_targets,
    }


def _empty_metrics() -> dict:
    return {
        "dependency_reuse_ratio": 0.0,
        "total_edges": 0,
        "declarations_with_in_degree": 0,
        "average_fan_in": 0.0,
        "average_fan_out": 0.0,
        "max_fan_in": 0,
        "max_fan_out": 0,
        "shared_targets_count": 0,
    }
