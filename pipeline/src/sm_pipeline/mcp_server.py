"""
Optional MCP server: tool "list_declarations_for_paper"
(read manifest/theorem_cards).
Run with: uv run --project pipeline python -m sm_pipeline.mcp_server
Requires: uv sync --extra mcp (or pip install mcp).
Not a CI gate; see docs/mcp-lean-tooling.md.
"""

import json
import sys
from pathlib import Path

TOOL_DEFINITIONS = [
    {
        "name": "list_declarations_for_paper",
        "description": (
            "List formal declarations (Lean) for a paper by paper_id. "
            "Reads corpus/papers/<paper_id>/manifest.json and "
            "theorem_cards.json. No Lean LSP required."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["paper_id"],
            "properties": {
                "paper_id": {
                    "type": "string",
                    "description": "Paper ID (e.g. langmuir_1918_adsorption)",
                }
            },
        },
    },
    {
        "name": "list_declarations_in_file",
        "description": (
            "List declarations for a paper that appear in a given file "
            "(filter theorem_cards by file_path). No Lean LSP required."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["paper_id", "file_path"],
            "properties": {
                "paper_id": {"type": "string"},
                "file_path": {
                    "type": "string",
                    "description": (
                        "Path or substring (e.g. Langmuir1918.lean)"
                    ),
                },
            },
        },
    },
    {
        "name": "get_dependency_graph_for_declaration",
        "description": (
            "Get dependency_ids and theorem card(s) for a declaration "
            "by paper_id and lean_decl. Reads manifest and theorem_cards; "
            "no Lean LSP required."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["paper_id", "lean_decl"],
            "properties": {
                "paper_id": {"type": "string"},
                "lean_decl": {
                    "type": "string",
                    "description": "Fully qualified Lean declaration name",
                },
            },
        },
    },
]


def get_tool_definitions() -> list[dict]:
    """Return MCP tool descriptors (used by tests and server runtime)."""
    return list(TOOL_DEFINITIONS)


def _repo_root() -> Path:
    """Assume run from repo root or pipeline dir; find repo root."""
    cwd = Path.cwd().resolve()
    for d in [cwd, cwd.parent]:
        if (d / "corpus" / "papers").is_dir():
            if (d / "corpus" / "index.json").exists():
                return d
    return cwd


def _list_declarations_for_paper(paper_id: str) -> list[dict]:
    """
    Read manifest.json and theorem_cards.json for paper_id; return list of
    declarations (lean_decl, file_path, proof_status, claim_id).
    """
    root = _repo_root()
    paper_dir = root / "corpus" / "papers" / paper_id
    if not paper_dir.is_dir():
        return []
    out: list[dict] = []
    manifest_path = paper_dir / "manifest.json"
    if manifest_path.exists():
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            for decl in data.get("declaration_index") or []:
                if isinstance(decl, str):
                    out.append({"lean_decl": decl, "source": "manifest"})
        except (json.JSONDecodeError, OSError):
            pass
    cards_path = paper_dir / "theorem_cards.json"
    if cards_path.exists():
        try:
            data = json.loads(cards_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for card in data:
                    if isinstance(card, dict):
                        out.append(
                            {
                                "lean_decl": card.get("lean_decl"),
                                "file_path": card.get("file_path"),
                                "proof_status": card.get("proof_status"),
                                "claim_id": card.get("claim_id"),
                                "source": "theorem_cards",
                            }
                        )
        except (json.JSONDecodeError, OSError):
            pass
    return out


def _list_declarations_in_file(paper_id: str, file_path: str) -> list[dict]:
    """
    Return declarations from theorem_cards (and manifest) for paper_id whose
    file_path matches the given path (substring match). No Lean LSP required.
    """
    all_decls = _list_declarations_for_paper(paper_id)
    if not file_path or not file_path.strip():
        return all_decls
    fp = file_path.strip().replace("\\", "/")
    return [
        d
        for d in all_decls
        if d.get("file_path")
        and fp in d.get("file_path", "").replace("\\", "/")
    ]


def _get_dependency_graph_for_declaration(paper_id: str, lean_decl: str) -> dict:
    """
    Return dependency_ids and related theorem card(s) for a declaration.
    Reads manifest and theorem_cards only; no Lean LSP required.
    """
    root = _repo_root()
    paper_dir = root / "corpus" / "papers" / paper_id
    if not paper_dir.is_dir():
        return {"lean_decl": lean_decl, "error": "paper not found"}
    result: dict = {
        "lean_decl": lean_decl,
        "paper_id": paper_id,
        "dependency_ids": [],
        "cards": [],
        "manifest_dependency_graph": None,
    }
    manifest_path = paper_dir / "manifest.json"
    if manifest_path.exists():
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            dg = data.get("dependency_graph")
            if dg is not None:
                result["manifest_dependency_graph"] = dg
        except (json.JSONDecodeError, OSError):
            pass
    cards_path = paper_dir / "theorem_cards.json"
    if cards_path.exists():
        try:
            data = json.loads(cards_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for card in data:
                    if not isinstance(card, dict):
                        continue
                    if card.get("lean_decl") == lean_decl:
                        result["cards"].append(card)
                        dep_ids = card.get("dependency_ids") or []
                        for did in dep_ids:
                            if did not in result["dependency_ids"]:
                                result["dependency_ids"].append(did)
        except (json.JSONDecodeError, OSError):
            pass
    return result


def _call_tool_payload(name: str, arguments: dict | None) -> object:
    """Pure-python tool dispatcher for testability."""
    args = arguments or {}
    if name == "list_declarations_for_paper":
        paper_id = args.get("paper_id")
        if not paper_id or not isinstance(paper_id, str):
            return "Missing required argument: paper_id"
        return _list_declarations_for_paper(paper_id)
    if name == "list_declarations_in_file":
        paper_id = args.get("paper_id")
        file_path = args.get("file_path")
        if not paper_id or not isinstance(paper_id, str):
            return "Missing required argument: paper_id"
        fp = (file_path or "").strip() if isinstance(file_path, str) else ""
        return _list_declarations_in_file(paper_id, fp)
    if name == "get_dependency_graph_for_declaration":
        paper_id = args.get("paper_id")
        lean_decl = args.get("lean_decl")
        if not paper_id or not isinstance(paper_id, str):
            return "Missing required argument: paper_id"
        if not lean_decl or not isinstance(lean_decl, str):
            return "Missing required argument: lean_decl"
        return _get_dependency_graph_for_declaration(paper_id, lean_decl)
    return f"Unknown tool: {name}"


def _run_server() -> None:
    """Run MCP server over stdio (requires mcp package)."""
    try:
        from mcp.server.lowlevel import Server
        from mcp.server.stdio import stdio_server
        from mcp import types
        import anyio
    except ImportError:
        sys.stderr.write(
            "MCP server requires the mcp package. Install with:\n"
            "  uv sync --extra mcp   (from repo root)\n"
            "  or: pip install mcp\n"
        )
        sys.exit(1)

    server = Server("scientific-memory-mcp")

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [types.Tool(**tool) for tool in get_tool_definitions()]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict | None
    ) -> list[types.TextContent]:
        payload = _call_tool_payload(name, arguments)
        if isinstance(payload, str):
            return [types.TextContent(type="text", text=payload)]
        return [
            types.TextContent(type="text", text=json.dumps(payload, indent=2))
        ]

    async def main() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    anyio.run(main)


if __name__ == "__main__":
    _run_server()
