set shell := ["bash", "-cu"]

# Diagnose environment (run when setup or check fails)
doctor:
	@echo "==> doctor: checking tool versions"
	@echo -n "uv: " && uv --version
	@echo -n "pnpm: " && pnpm --version
	@echo -n "lean: " && (lake env lean --version 2>/dev/null || echo "not found (run from repo root with elan/lake in PATH)")
	@echo -n "lake: " && (lake --version 2>/dev/null || echo "not found")
	@echo "==> doctor done"

bootstrap:
	./scripts/bootstrap.sh

build:
	lake build
	pnpm --dir portal build
	uv run --project pipeline pytest
	uv run --project kernels/adsorption pytest

# Lean build only (use for local verification; CI runs full build)
lake-build:
	lake build

# Lean build with log to file (diagnostic)
lake-build-verbose LOG='lake-build.log':
	lake build 2>&1 | tee "{{LOG}}"

fmt:
	lake fmt
	uv run --project pipeline ruff format .
	pnpm --dir portal format

lint:
	uv run --project pipeline ruff check .
	pnpm --dir portal lint

validate:
	uv run --project pipeline python -m sm_pipeline.cli validate-all

# Regenerate docs/status/repo-snapshot.md from corpus manifests
repo-snapshot:
	uv run python scripts/generate_repo_snapshot.py

# Alias for SPEC 17 contributor flow
validate-corpus:
	just validate

portal:
	pnpm --dir portal dev

test:
	uv run --project pipeline pytest
	uv run --project kernels/adsorption pytest
	bash tests/smoke/test_repo_bootstrap.sh

benchmark:
	uv run --project pipeline python -m sm_pipeline.cli benchmark

# Quick benchmark smoke test (SPEC 17)
benchmark-smoke:
	uv run --project pipeline python -m sm_pipeline.cli benchmark

check:
	@echo "==> fmt"
	just fmt
	@echo "==> lint"
	just lint
	@echo "==> validate"
	just validate
	@echo "==> test"
	just test
	@echo "==> build"
	just build
	@echo "==> check complete"

add-paper PAPER_ID:
	uv run --project pipeline python -m sm_pipeline.cli add-paper {{PAPER_ID}}

build-index:
	uv run --project pipeline python -m sm_pipeline.cli build-index

hash-source PAPER_ID='':
	uv run --project pipeline python -m sm_pipeline.cli hash-source {{ if PAPER_ID != '' { '--paper-id ' + PAPER_ID } else { '' } }}

extract-claims PAPER_ID:
	uv run --project pipeline python -m sm_pipeline.cli extract-claims --paper-id {{PAPER_ID}}

normalize-paper PAPER_ID:
	uv run --project pipeline python -m sm_pipeline.cli normalize-paper --paper-id {{PAPER_ID}}

generate-mapping PAPER_ID:
	uv run --project pipeline python -m sm_pipeline.cli generate-mapping --paper-id {{PAPER_ID}}

scaffold-formal PAPER_ID:
	uv run --project pipeline python -m sm_pipeline.cli scaffold-formal --paper-id {{PAPER_ID}}

publish-artifacts PAPER_ID:
	uv run --project pipeline python -m sm_pipeline.cli publish --paper-id {{PAPER_ID}}

export-portal-data:
	uv run --project pipeline python -m sm_pipeline.cli export-portal-data

# Scaffold benchmarks/gold/<PAPER_ID>/ from corpus (claims, source_spans, assumptions). Run when adding gold for a new paper (SPEC 12).
scaffold-gold PAPER_ID:
	uv run --project pipeline python -m sm_pipeline.cli scaffold-gold --paper-id {{PAPER_ID}}

# Validate full corpus (ensures PAPER_ID's files are valid) (SPEC 17)
check-paper PAPER_ID:
	just validate-corpus

# Optional: report blueprint vs mapping.json mismatches (SPEC 8.4)
check-paper-blueprint PAPER_ID:
	uv run --project pipeline python -m sm_pipeline.cli check-paper-blueprint {{PAPER_ID}}

# Export current corpus state to corpus/snapshots/last-release.json for Diff page
export-diff-baseline:
	uv run --project pipeline python -m sm_pipeline.cli export-diff-baseline

intake-report PAPER_ID:
	uv run --project pipeline python -m sm_pipeline.cli intake-report --paper-id {{PAPER_ID}}

extraction-report PAPER_ID:
	uv run --project pipeline python -m sm_pipeline.cli extraction-report --paper-id {{PAPER_ID}}

ambiguity-flags PAPER_ID *ARGS:
	uv run --project pipeline python -m sm_pipeline.cli ambiguity-flags --paper-id {{PAPER_ID}} {{ARGS}}

# Optional: check pandoc availability (for extract-from-source)
check-tooling:
	uv run --project pipeline python -m sm_pipeline.cli check-tooling

# Optional: pandoc source/main.tex -> suggested_claims.json (human review)
extract-from-source PAPER_ID:
	uv run --project pipeline python -m sm_pipeline.cli extract-from-source {{PAPER_ID}}

# Optional: build Verso long-form docs (Verso is a Lake dependency; see lakefile.toml and docs/contributor-playbook.md#verso-integration-optional).
build-verso:
	-lake exe generate-site
	@echo "If the above failed: run 'lake build' after a successful 'lake update', then retry. See docs/contributor-playbook.md#verso-integration-optional for network and Windows notes."

# Run lake update without fetching mathlib cache (use when cache fetch fails, e.g. Windows CRYPT_E_NO_REVOCATION_CHECK). First build will be slower. See docs/contributor-playbook.md#verso-integration-optional. If 'lake' is not found (e.g. in Git Bash), run the same command in a shell where elan/lake is in PATH, or run: MATHLIB_NO_CACHE_ON_UPDATE=1 lake update
lake-update-no-cache:
	MATHLIB_NO_CACHE_ON_UPDATE=1 lake update

# Optional: run MCP server (requires: uv sync --extra mcp). Tools: list_declarations_for_paper, list_declarations_in_file, get_dependency_graph_for_declaration. See docs/mcp-lean-tooling.md.
mcp-server:
	uv run --project pipeline python -m sm_pipeline.mcp_server

# Derived metrics from corpus (SPEC 12): median intake time, dependency reuse, symbol conflict
metrics *ARGS:
	uv run --project pipeline python -m sm_pipeline.cli metrics {{ARGS}}
