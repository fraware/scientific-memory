# Scientific Memory — convenience targets (primary recipes live in JUSTFILE).

PCS_CORE ?= ../pcs-core
LABTRUST_OUT ?= benchmark_runs/labtrust_rendering
LABTRUST_CASES ?= benchmarks/rendering/labtrust_qc_release
INGEST ?= $(LABTRUST_OUT)/pcs_bench_ingest.v0.json

.PHONY: pcs-bench-producer pcs-bench-producer-external

# Release-grade PCS benchmark producer: render + validate ingest for pcs-bench gate.
pcs-bench-producer:
	uv run python scripts/run_pcs_bench_producer_gate.py --require-pcs-bench-cli

# Full external-reviewer packet (exercises failure/comparison/staleness metrics).
pcs-bench-producer-external:
	uv run python scripts/run_pcs_bench_producer_gate.py \
		--cases benchmarks/rendering/external_reviewer_minimal \
		--out benchmark_runs/external_reviewer_minimal \
		--require-pcs-bench-cli
