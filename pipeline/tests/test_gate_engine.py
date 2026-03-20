"""Gate engine runs the same validation sequence as validate_repo."""

from pathlib import Path

from sm_pipeline.validate.gate_engine import run_all_gates


def test_run_all_gates_ok_on_repo() -> None:
    repo = Path(__file__).resolve().parents[2]
    report = run_all_gates(repo)
    assert report.ok
    assert any(s.check_id == "json_schemas_and_kernels" for s in report.steps)


def test_gate_report_json_roundtrip() -> None:
    from sm_pipeline.validate.gate_engine import GateReport

    r = GateReport(repo_root="/tmp", ok=True, steps=[], warnings=["w"])
    d = r.to_json_dict()
    assert d["repo_root"] == "/tmp"
    assert d["warnings"] == ["w"]
