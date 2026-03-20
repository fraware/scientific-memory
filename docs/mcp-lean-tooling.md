# MCP / LSP Lean tooling (partial only)

SPEC Section 6 describes optional MCP/LSP-based Lean tooling. **What ships today is intentionally partial:** a small, read-only MCP server that answers questions from **published JSON** (`manifest.json`, `theorem_cards.json`) only. It is **not** a Lean language server, does not parse `formal/`, and does not call `lake` or the Lean LSP.

Use this page for the integration contract, limitations, and how to run or extend the optional server.

## What is implemented (partial)

| Area | Implemented | Not implemented |
|------|-------------|-----------------|
| MCP over stdio | Yes (`sm_pipeline.mcp_server`) | Resource templates, prompts, sampling |
| Declaration listing | By `paper_id`; by `file_path` substring on **theorem_cards** rows that carry `file_path` | Listing from Lean AST or LSP |
| Dependencies | `dependency_ids` on the matching theorem card(s); optional full `manifest_dependency_graph` from manifest | Per-declaration graph slice computed from Lean; transitive closure helpers |
| Data source | `corpus/papers/<paper_id>/manifest.json`, `theorem_cards.json` | Live `formal/*.lean`, `#check`, tactic state |

**Tools (three):**

1. **`list_declarations_for_paper(paper_id)`** — Merges `declaration_index` strings from the manifest with entries from `theorem_cards.json` (see [Declaration record shape](#declaration-record-shape)).
2. **`list_declarations_in_file(paper_id, file_path)`** — Filters the merged list to rows where `file_path` exists and contains the given substring (normalized to `/`). Rows sourced only from the manifest (no `file_path`) **do not** match file filters.
3. **`get_dependency_graph_for_declaration(paper_id, lean_decl)`** — Finds theorem card(s) for `lean_decl`, returns their `dependency_ids`, embedded `cards`, and if present the entire manifest `dependency_graph` field as `manifest_dependency_graph` (not a Lean-computed subgraph).

**Run (optional extra):**

```bash
uv sync --extra mcp
just mcp-server
# or: uv run --project pipeline python -m sm_pipeline.mcp_server
```

The server discovers the repo root by walking upward from the current working directory for a tree that contains `corpus/papers` and `corpus/index.json`. **Run from the repository root** (or a parent that satisfies that layout) so paths resolve correctly.

**CI:** MCP is not a merge gate for `just build` / `just validate`. Contract tests run in `.github/workflows/mcp-contract.yml` after `uv sync --extra mcp` (`pipeline/tests/test_mcp_server_contract.py`, `test_mcp_server_data_paths.py`). For the same commands locally, see [Contributor playbook – Local CI](contributor-playbook.md#local-ci-checklist-green-before-merge).

## LSP (out of scope for this MCP layer)

- **Editor LSP:** Lean 4 LSP is provided by the [vscode-lean4](https://github.com/leanprover/vscode-lean4) extension (or similar). This repo does not configure or ship LSP for agents.
- **“Full LSP” in SPEC sense:** Querying types, hovers, or declaration lists **from** the Lean server **via** MCP or the pipeline is **not** implemented and remains deferred. The current MCP tools are a **corpus/manifest mirror**, not a Lean bridge.

## Partial integration contract (what we guarantee today)

1. **Optional only:** Must not be required for `just build`, `just validate`, or portal CI.
2. **Read-only:** Tools only read JSON under `corpus/papers/...`; they do not mutate corpus, formal, or schemas.
3. **Source of truth:** The same artifacts validated by the gate engine; MCP may lag until `just publish-artifacts` / export paths have run. Do not treat MCP output as stronger than the committed manifest and theorem cards.
4. **No semantic Lean guarantees:** Absence from a tool result does not mean a declaration does not exist in Lean; presence of `dependency_ids` reflects published cards, not a full static analysis of imports.
5. **Documentation:** Entrypoint and shapes are defined here and in [`mcp_server.py`](../pipeline/src/sm_pipeline/mcp_server.py) (`TOOL_DEFINITIONS`, `_call_tool_payload`). Architecture overview: [architecture.md](architecture.md).

## Limitations agents and reviewers should know

- **Duplicates / merge semantics:** `list_declarations_for_paper` can list the same logical declaration twice (once from `declaration_index`, once from theorem cards) with different `source` values. Consumers must dedupe or prefer `theorem_cards` when richer fields are needed.
- **File path filter:** Substring match only; not a canonical path resolver. Wrong CWD can yield empty results even when the paper exists.
- **Dependency tool:** `manifest_dependency_graph` is passed through wholesale when the manifest has it; the server does not filter it to neighbors of `lean_decl`. For “what depends on this,” you only get explicit `dependency_ids` on the card.
- **Errors:** Missing paper or malformed JSON yields empty lists or payloads with `error` / partial fields; callers should handle empty results.

## Declaration record shape

The `list_declarations_for_paper` and `list_declarations_in_file` tools return a list of declaration records. Each record is a dict with the following shape:

**From manifest (`source: "manifest"`):**

- `lean_decl` (str): Full declaration name (e.g. `ScientificMemory.Chemistry.Adsorption.Langmuir1918.langmuir_isotherm`)
- `source` (str): Always `"manifest"`

**From theorem_cards (`source: "theorem_cards"`):**

- `lean_decl` (str): Full declaration name
- `file_path` (str | None): Path to Lean file relative to repo root
- `proof_status` (str | None): Proof status (e.g. `"machine_checked"`)
- `claim_id` (str | None): Linked claim ID
- `source` (str): Always `"theorem_cards"`

Consumers should check `source` to decide which fields are available. Manifest-sourced records are minimal; theorem_cards-sourced records include file path, proof status, and claim linkage.

## Recommended agent loop (human-in-the-loop)

1. **List declarations:** `list_declarations_for_paper` or `list_declarations_in_file`.
2. **Graph context:** `get_dependency_graph_for_declaration` (interpret as published `dependency_ids` + optional full manifest graph).
3. **Propose change:** Agent emits a `proof_repair_apply_bundle` or a normal PR diff. **Never** auto-apply without human review.
4. **Human PR:** Reviewer runs `lake build`, `validate-all`, and merges. See ADR [0007-agentic-worker-interface.md](adr/0007-agentic-worker-interface.md) and [Verification boundary](contributor-playbook.md#verification-boundary) in the contributor playbook.

## Roadmap beyond partial (not committed)

When tightening SPEC alignment, consider (in rough order):

1. **Lake / Lean-backed tools** (optional): subprocess or client to answer queries from `formal/` (still not a default CI gate).
2. **LSP-backed read tools:** types, signatures, or declaration lists via Lean LSP (heavy operational cost; needs explicit maintainer decision).
3. **Narrower graph API:** return a bounded subgraph around `lean_decl` from manifest data only, or document how to use `manifest_dependency_graph` safely.
4. **De-duplication strategy:** optional flag or stable merge rules for manifest vs theorem_cards listing.

Track prioritization in [ROADMAP.md](../ROADMAP.md) and update this file when behavior changes.

## Implementation checklist (partial layer)

- [x] Python MCP server + optional `mcp` extra in `pipeline/pyproject.toml`.
- [x] `list_declarations_for_paper`, `list_declarations_in_file`, `get_dependency_graph_for_declaration` (corpus JSON only).
- [x] `just mcp-server` and documented install path.
- [x] Optional CI lane `mcp-contract.yml` for contract tests.
- [ ] Full LSP or Lean-backed MCP tools (deferred).
- [ ] Type/signature tool (deferred).

## References

- SPEC Section 6: optional MCP/LSP-based Lean tooling (full vision vs this partial slice).
- [Contributor playbook – Local CI](contributor-playbook.md#local-ci-checklist-green-before-merge) for MCP test commands.
- Lean editor LSP: [vscode-lean4](https://github.com/leanprover/vscode-lean4) and Lake documentation.
