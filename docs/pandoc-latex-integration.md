# Pandoc / LaTeX integration

SPEC Section 6 lists "pandoc, LaTeX parsers, XML/HTML utilities as needed" for the pipeline layer. Extraction remains **human-curated or script-based** for CI; see [ADR 0008](adr/0008-llm-worker-deferred.md). Optional pandoc-based extraction is available.

## Current state

- **Tooling check:** `just check-tooling` reports whether pandoc is available (optional; not a CI gate).
- **Optional extraction:** With pandoc and `corpus/papers/<paper_id>/source/main.tex`, run `just extract-from-source <paper_id>` to generate `suggested_claims.json`: one suggested claim per section heading, plus `candidate_equations` (from pandoc Math nodes), `candidate_symbols` (from equation content), and `macro_context` (from RawBlock preamble: `\newcommand` / `\def` collected for human review). Merge into claims.json and symbols as needed. See [paper-intake](paper-intake.md) and [generated-artifacts](generated-artifacts.md).
- Full LaTeX AST parsing (custom macros, deep structure): optional macro context is implemented (collection only); expansion is not performed. Full macro expansion is accepted as optional (not required for v0.1). See [ROADMAP.md](../ROADMAP.md); ADR 0008 documents LLM/worker as deferred.

### Limitations

Custom LaTeX macros (e.g. `\newcommand{\foo}{...}`, `\def`) are **not** expanded by the current pipeline. The extractor collects macro definitions from pandoc RawBlocks and attaches `macro_context` to each suggested claim for human review; equation and symbol extraction still see the macro name or unexpanded form in math content. Future tooling may use macro_context to optionally expand or tag macro-derived content.

## Integration contract (when implemented)

1. **Input:** Source files under a paper directory (e.g. `source/main.tex`, `source/paper.pdf`) with a documented layout.
2. **Pandoc:** If pandoc is available, a pipeline step may run `pandoc source/main.tex -o intermediate.json` (or similar) to obtain a structured representation. The step must be optional (graceful no-op if pandoc is missing or the file is absent).
3. **LaTeX:** Parsing may use pandoc, a LaTeX AST library (e.g. pylatexenc, or a subprocess to a LaTeX-aware tool), or an external service. Output must align with the claim/assumption/symbol schema so that extraction can merge or compare with hand-curated data.
4. **No gate:** Pandoc/LaTeX parsing must not be a CI gate in v0.1. It can be an optional `just extract-from-source <paper_id>` that writes suggested claims/assumptions for human review.
5. **Generator contract:** Any generated corpus file (e.g. suggested claims) must be documented in [generated-artifacts](generated-artifacts.md) and reproducible.

## Optional: availability check

A minimal "state of the art" step is to **detect** whether pandoc is available and record it in metrics or a small report (e.g. `just metrics` or a dedicated `just check-tooling`). That does not parse content but informs contributors and docs. Example:

```bash
which pandoc && pandoc --version
```

If you add such a check, document it in [metrics](metrics.md) or [contributor-playbook](contributor-playbook.md) as optional tooling.

## Steps to add pandoc/LaTeX later

1. Add pandoc (and optionally a LaTeX parser) as an optional dependency; document in README.
2. Define the expected source layout (e.g. `source/main.tex`) in [paper-intake](paper-intake.md).
3. Implement a pipeline module that runs pandoc on the source and emits a structured representation (e.g. JSON with sections and equations).
4. Add an extraction step that maps that representation to suggested claims/assumptions/symbols (or a diff against existing corpus) for human review.
5. Document the generator in [generated-artifacts](generated-artifacts.md) and note any scope change in [ROADMAP.md](../ROADMAP.md).

## References

- SPEC Section 6 (pipeline: "pandoc, LaTeX parsers, XML/HTML utilities as needed").
- [ADR 0008](adr/0008-llm-worker-deferred.md): extraction human/script-curated.
- Full LaTeX macro parsing is an optional limitation (this doc and SPEC Section 6).
