# Wrapper sources scripts/just_env.sh so uv/node/pnpm stay on PATH (no nested just).
# Windows: use Git Bash, not WSL bash (Windows node/pnpm resolve /c/... correctly).
set shell := ["bash", "scripts/just_shell_wrapper.sh", "-cu"]
set windows-shell := ["C:/Program Files/Git/bin/bash.exe", "scripts/just_shell_wrapper.sh", "-cu"]

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
	@echo "==> build"
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
	@echo "==> fmt"
	bash scripts/lake_fmt_optional.sh
	uv run --project pipeline ruff format .
	pnpm --dir portal format

lint:
	@echo "==> lint"
	uv run --project pipeline ruff check .
	pnpm --dir portal lint

validate:
	@echo "==> validate"
	uv run --project pipeline python -m sm_pipeline.cli validate-all

# Regenerate docs/status/repo-snapshot.md from corpus manifests
repo-snapshot:
	uv run python scripts/generate_repo_snapshot.py

# Alias for SPEC 17 contributor flow (same as validate; no nested just)
validate-corpus: validate

# Install portal deps when next is missing (skips if node_modules already usable)
portal-install:
	bash scripts/portal_install.sh

portal-stop:
	bash scripts/portal_stop.sh

portal-clean:
	rm -rf portal/.next

portal: portal-install
	bash scripts/portal_dev.sh

test:
	@echo "==> test"
	uv run --project pipeline pytest
	uv run --project kernels/adsorption pytest
	bash tests/smoke/test_repo_bootstrap.sh

# PCS LabTrust import contract tests (also run via `just test`)
test-pcs:
	@echo "==> test-pcs"
	bash scripts/sm_python.sh scripts/verify_labtrust_release_fixture.py
	python scripts/verify_tool_use_release_fixture.py
	bash scripts/run_pcs_tests.sh
	node portal/scripts/verify-pcs-read-model.mjs
	pnpm --dir portal test:pcs-phase2-contract
	pnpm --dir portal test:pcs-tool-use-phase2-contract

# PCS v0.1 gate: contract tests + corpus validation (fixtures are committed; no refresh)
pcs-verify: test-pcs
	bash scripts/sm_python.sh -m sm_pipeline.cli validate-all

# Atomic PCS v0.1: sync from canonical pcs-core/examples/labtrust-release/ only
refresh-pcs-release:
	bash scripts/sm_python.sh scripts/sync_pcs_schemas.py
	bash scripts/sm_python.sh scripts/sync_labtrust_release_from_pcs_core.py
	python scripts/sync_tool_use_release_from_pcs_core.py --ensure
	bash scripts/sm_python.sh scripts/ensure_labtrust_phase2_fixtures.py
	bash scripts/sm_python.sh scripts/ensure_labtrust_phase2_fixtures.py --release-dir release-run
	bash scripts/sm_python.sh scripts/regenerate_labtrust_negative_fixtures.py
	bash scripts/sm_python.sh scripts/verify_labtrust_release_fixture.py --write
	bash scripts/sm_python.sh scripts/refresh_pcs_canonical_fixture.py --copy-to-fixture --sync-pcs-core-alias

# Legacy alias (do not vendor repo-by-repo; use refresh-pcs-release)
refresh-pcs-fixtures: refresh-pcs-release

refresh-pcs-corpus:
	bash scripts/sm_python.sh scripts/refresh_pcs_corpus_from_release.py

refresh-pcs-corpus-legacy:
	bash scripts/sm_python.sh scripts/refresh_pcs_corpus_demo.py

benchmark:
	uv run --project pipeline python -m sm_pipeline.cli benchmark

# Quick benchmark smoke test (SPEC 17)
benchmark-smoke:
	uv run --project pipeline python -m sm_pipeline.cli benchmark

# Recipe dependencies avoid nested `just` subprocesses (fixes PATH on Windows).
check: fmt lint validate test build
	@echo "==> check complete"

# Canonical local contribution path.
canonical-local: bootstrap check benchmark
	@echo "==> canonical-local complete"

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
check-paper PAPER_ID: validate-corpus

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

# Optional: Prime Intellect LLM proposal sidecars (API key in root `.env`; see docs/tooling/prime-intellect-llm.md)
llm-claim-proposals PAPER_ID:
	uv run --project pipeline python -m sm_pipeline.cli llm-claim-proposals --paper-id {{PAPER_ID}}

llm-mapping-proposals PAPER_ID:
	uv run --project pipeline python -m sm_pipeline.cli llm-mapping-proposals --paper-id {{PAPER_ID}}

# Optional: surgical Lean find/replace suggestions (sidecar only; convert then proof-repair-apply after review)
llm-lean-proposals PAPER_ID:
	uv run --project pipeline python -m sm_pipeline.cli llm-lean-proposals --paper-id {{PAPER_ID}}

# Optional: LLM smoke/live eval report (writes benchmarks/reports/llm_live_*.json; dir is gitignored)
llm-live-eval *ARGS:
	uv run python scripts/llm_live_eval.py {{ARGS}}

# Optional: full lake build when LLM_EVAL_RUN_LAKE_BUILD=1 (manual sanity after Lean-related eval)
llm-eval-lean-build-optional:
	uv run python scripts/llm_eval_lean_build_optional.py

# Optional: build Verso long-form docs (Verso is a Lake dependency; see lakefile.toml and docs/contributor-playbook.md#verso-integration-optional).
build-verso:
	-lake exe generate-site
	@echo "If the above failed: run 'lake build' after a successful 'lake update', then retry. See docs/contributor-playbook.md#verso-integration-optional for network and Windows notes."

# Run lake update without fetching mathlib cache (use when cache fetch fails, e.g. Windows CRYPT_E_NO_REVOCATION_CHECK). First build will be slower. See docs/contributor-playbook.md#verso-integration-optional. If 'lake' is not found (e.g. in Git Bash), run the same command in a shell where elan/lake is in PATH, or run: MATHLIB_NO_CACHE_ON_UPDATE=1 lake update
lake-update-no-cache:
	MATHLIB_NO_CACHE_ON_UPDATE=1 lake update

# Optional: run MCP server (requires: uv sync --extra mcp). Tools: list_declarations_for_paper, list_declarations_in_file, get_dependency_graph_for_declaration. See docs/tooling/mcp-lean-tooling.md.
mcp-server:
	uv run --project pipeline python -m sm_pipeline.mcp_server

# Derived metrics from corpus (SPEC 12): median intake time, dependency reuse, symbol conflict
metrics *ARGS:
	uv run --project pipeline python -m sm_pipeline.cli metrics {{ARGS}}

# Canonical RC + Phase 2 gate (drift, import-release, portal contracts); requires pcs-core checkout
pcs-rc-gate:
	bash scripts/run_pcs_rc_ci_gate.sh

# Cross-platform PCS gate (Windows-friendly)
pcs-rc-gate-py:
	python scripts/run_pcs_rc_gate.py

pcs-phase2-gate: pcs-rc-gate

# PCS LabTrust v0.1 (positional args; optional defaults on pcs-v01-clean-chain-sm)
#   just pcs-import-bundle tests/pcs/fixtures/labtrust-release/signed_science_claim_bundle.json
#   just pcs-render-claim claim-pcs-qc-release-v0.1
pcs-import-bundle bundle *FLAGS:
	bash scripts/sm_python.sh -m sm_pipeline.cli pcs-import-bundle --bundle "{{bundle}}" {{FLAGS}}

pcs-import-legacy-bundle bundle:
	bash scripts/sm_python.sh -m sm_pipeline.cli pcs-import-bundle --bundle "{{bundle}}" --allow-legacy

pcs-validate-bundle bundle:
	bash scripts/sm_python.sh -m sm_pipeline.cli pcs-validate-bundle --bundle "{{bundle}}"

pcs-render-claim claim_id:
	bash scripts/sm_python.sh -m sm_pipeline.cli pcs-render-claim --claim-id "{{claim_id}}"

# Optional: uv sync --project pipeline --extra pcs (requires ../../pcs-core/python)
sync-pipeline-pcs:
	@if [ -d "pcs-core/python" ] || [ -d "../pcs-core/python" ]; then \
		uv sync --native-tls --project pipeline --extra pcs; \
	else \
		echo "pcs-core not found; using schema mirrors only (legacy import still works)"; \
		uv sync --native-tls --project pipeline; \
	fi

# Copy canonical schemas from pcs-core (sibling ../pcs-core or repo pcs-core/)
sync-pcs-schemas:
	uv run python scripts/sync_pcs_schemas.py

pcs-import-labtrust-demo:
	just pcs-import-legacy-bundle tests/pcs/fixtures/valid_signed_science_claim_bundle.json

pcs-import-labtrust-release:
	just pcs-import-bundle tests/pcs/fixtures/labtrust-release/signed_science_claim_bundle.json --release-mode

# Canonical RC import (strict, non-legacy, fixture-pinned import report)
pcs-import-rc-bundle:
	just pcs-import-bundle tests/pcs/fixtures/labtrust-release/signed_science_claim_bundle.json --strict --release-mode

# Phase 2: import from ReleaseManifest.v0 (strict release mode)
pcs-import-release RELEASE_MANIFEST="tests/pcs/fixtures/labtrust-release/ReleaseManifest.v0.json":
	just pcs-import-release-manifest "{{RELEASE_MANIFEST}}"

sync-labtrust-release:
	python scripts/sync_labtrust_release_from_pcs_core.py --no-corpus

pcs-import-tool-use-release RELEASE_MANIFEST="tests/pcs/fixtures/tool-use-release/release_manifest.v0.json":
	just pcs-import-release-manifest "{{RELEASE_MANIFEST}}"

sync-tool-use-release:
	python scripts/sync_tool_use_release_from_pcs_core.py --ensure

pcs-import-release-manifest release_manifest:
	SM_FORCE_UV=1 bash scripts/sm_python.sh -m sm_pipeline.cli pcs-import-release --release-manifest "{{release_manifest}}"

pcs-list-claims:
	SM_FORCE_UV=1 bash scripts/sm_python.sh -m sm_pipeline.cli pcs-list-claims

pcs-show-claim claim_id="claim-pcs-qc-release-v0.1":
	SM_FORCE_UV=1 bash scripts/sm_python.sh -m sm_pipeline.cli pcs-show-claim --claim-id "{{claim_id}}"

pcs-check-stale claim_id="claim-pcs-qc-release-v0.1":
	SM_FORCE_UV=1 bash scripts/sm_python.sh -m sm_pipeline.cli pcs-check-stale --claim-id "{{claim_id}}"

pcs-list-claims-by-certificate certificate_id:
	SM_FORCE_UV=1 bash scripts/sm_python.sh -m sm_pipeline.cli pcs-list-claims-by-certificate --certificate-id "{{certificate_id}}"

pcs-list-claims-by-source-commit commit:
	SM_FORCE_UV=1 bash scripts/sm_python.sh -m sm_pipeline.cli pcs-list-claims-by-source-commit --commit "{{commit}}"

pcs-list-claims-by-release release_id:
	SM_FORCE_UV=1 bash scripts/sm_python.sh -m sm_pipeline.cli pcs-list-claims-by-release --release-id "{{release_id}}"

pcs-list-claims-by-workflow workflow_id:
	SM_FORCE_UV=1 bash scripts/sm_python.sh -m sm_pipeline.cli pcs-list-claims-by-workflow --workflow-id "{{workflow_id}}"

pcs-compare-releases old_release new_release:
	SM_FORCE_UV=1 bash scripts/sm_python.sh -m sm_pipeline.cli pcs-compare-releases --old-release "{{old_release}}" --new-release "{{new_release}}"

pcs-list-claims-by-trace-hash trace_hash:
	SM_FORCE_UV=1 bash scripts/sm_python.sh -m sm_pipeline.cli pcs-list-claims-by-trace-hash --trace-hash "{{trace_hash}}"

pcs-list-stale-claims:
	SM_FORCE_UV=1 bash scripts/sm_python.sh -m sm_pipeline.cli pcs-list-stale-claims

pcs-refresh-stale:
	SM_FORCE_UV=1 bash scripts/sm_python.sh -m sm_pipeline.cli pcs-refresh-stale

pcs-query-lineage *FLAGS:
	SM_FORCE_UV=1 bash scripts/sm_python.sh -m sm_pipeline.cli pcs-query-lineage {{FLAGS}}

# Tail of PCS v0.1 clean-checkout chain (after pf sign in LabTrust-Gym workdir)
pcs-v01-clean-chain-sm bundle="../LabTrust-Gym/signed_science_claim_bundle.json" claim_id="claim-pcs-qc-release-v0.1":
	just pcs-import-bundle "{{bundle}}"
	just pcs-render-claim "{{claim_id}}"

pcs-import-pcs-core-demo:
	just sync-pipeline-pcs
	just pcs-import-labtrust-release

pcs-refresh-demo: refresh-pcs-fixtures refresh-pcs-corpus
	just pcs-render-claim claim-pcs-qc-release-v0.1
	just pcs-render-claim labtrust-qc-release-claim-001

test-pcs-portal:
	pnpm --dir portal test:pcs-contract

# Live pcs-core validation (requires: just sync-pipeline-pcs first)
test-pcs-integration:
	just sync-pipeline-pcs
	bash scripts/run_pcs_integration_tests.sh
