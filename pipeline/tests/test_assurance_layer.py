"""Tests for assurance / autonomous science layer."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from assurance_fixtures import (
    base_calibration,
    base_outcome,
    make_node,
    write_release_bundle,
)
from sm_pipeline.assurance.export import (
    build_assurance_portal_export,
    export_action_chain,
    write_assurance_portal_export,
)
from sm_pipeline.assurance.graph import append_node, load_chain, validate_chain
from sm_pipeline.assurance.hashing import content_digest
from sm_pipeline.assurance.import_ import import_assurance_release
from sm_pipeline.assurance.metrics import compute_autonomous_science_metrics, reconcile_metric_slice
from sm_pipeline.assurance.mutations import add_calibration, add_outcome, add_replication_node
from sm_pipeline.assurance.validate import (
    AssuranceValidationError,
    calibration_to_portal_read_model,
    outcome_to_portal_read_model,
    reject_duplicate_outcome_id,
    validate_calibration_record,
    validate_outcome_record,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def tmp_repo(tmp_path: Path) -> Path:
    """Minimal repo root with schemas/assurance copied."""
    schemas_src = REPO_ROOT / "schemas" / "assurance"
    schemas_dst = tmp_path / "schemas" / "assurance"
    shutil.copytree(schemas_src, schemas_dst)
    (tmp_path / "corpus" / "assurance" / "actions").mkdir(parents=True)
    (tmp_path / "corpus" / "assurance" / "index.json").write_text(
        json.dumps({"schema_version": "v1", "action_ids": []}) + "\n",
        encoding="utf-8",
    )
    (tmp_path / "corpus" / "pcs" / "claims").mkdir(parents=True)
    (tmp_path / "portal" / ".generated").mkdir(parents=True)
    return tmp_path


def test_outcome_valid_and_portal_read_model(tmp_repo: Path) -> None:
    outcome = base_outcome("action-a", "outcome-1")
    record = validate_outcome_record(tmp_repo, outcome)
    rm = outcome_to_portal_read_model(record)
    assert rm["outcome_id"] == "outcome-1"
    assert "does not constitute claim acceptance" in rm["non_claim"]


def test_outcome_digest_mismatch(tmp_repo: Path) -> None:
    outcome = base_outcome("action-a", "outcome-1")
    outcome["integrity"]["content_digest"] = "sha256:" + ("b" * 64)
    with pytest.raises(AssuranceValidationError, match="digest mismatch"):
        validate_outcome_record(tmp_repo, outcome)


def test_outcome_unknown_schema_version(tmp_repo: Path) -> None:
    outcome = base_outcome("action-a", "outcome-1")
    outcome["schema_version"] = "v99"
    with pytest.raises(AssuranceValidationError, match="schema_version"):
        validate_outcome_record(tmp_repo, outcome)


def test_outcome_missing_required_id(tmp_repo: Path) -> None:
    outcome = base_outcome("action-a", "outcome-1")
    del outcome["outcome_id"]
    # reseal would be needed; without id schema fails
    with pytest.raises(AssuranceValidationError):
        validate_outcome_record(tmp_repo, outcome)


def test_duplicate_outcome_id_helper() -> None:
    with pytest.raises(AssuranceValidationError, match="Duplicate"):
        reject_duplicate_outcome_id({"outcome-1"}, "outcome-1")


def test_calibration_missing_prediction_explicit(tmp_repo: Path) -> None:
    cal = base_calibration(
        "action-a",
        "cal-1",
        prediction_presence={
            "success": False,
            "information_gain": False,
            "cost": False,
            "time": False,
            "risk": False,
        },
        predicted_success=None,
        predicted_information_gain=None,
        predicted_cost=None,
        predicted_time=None,
        predicted_risk=None,
        aggregation_eligibility=False,
        realized_outcome_id=None,
        calibration_class="not_aggregable",
        missingness={
            "has_missing_fields": True,
            "fields": [{"field": "predictions", "reason": "not available"}],
        },
    )
    record = validate_calibration_record(tmp_repo, cal)
    assert record.predicted_success is None
    rm = calibration_to_portal_read_model(record)
    assert rm["prediction_presence"]["success"] is False


def test_calibration_rejects_omitted_presence_map(tmp_repo: Path) -> None:
    cal = base_calibration("action-a", "cal-1")
    del cal["prediction_presence"]
    with pytest.raises(AssuranceValidationError, match="prediction_presence"):
        validate_calibration_record(tmp_repo, cal)


def test_calibration_rejects_aggregation_without_realized(tmp_repo: Path) -> None:
    from sm_pipeline.assurance.validate import seal_integrity

    cal = base_calibration("action-a", "cal-bad")
    cal["aggregation_eligibility"] = True
    cal["realized_outcome_id"] = None
    cal = seal_integrity(cal, writer_identity="t", created_at="2026-07-01T00:00:00Z")
    with pytest.raises(AssuranceValidationError, match="aggregation_eligibility"):
        validate_calibration_record(tmp_repo, cal)


def test_import_and_validate_chain(tmp_repo: Path, tmp_path: Path) -> None:
    release = write_release_bundle(tmp_path / "release", "action-demo")
    report = import_assurance_release(release, repo_root=tmp_repo, write=True)
    assert report.ok
    result = validate_chain(tmp_repo, "action-demo")
    assert result["ok"]
    assert result["acyclic"]


def test_import_digest_mismatch(tmp_repo: Path, tmp_path: Path) -> None:
    release = write_release_bundle(tmp_path / "release-bad", "action-bad")
    # corrupt one file after checksums written
    node_path = next((release / "nodes").glob("*.json"))
    data = json.loads(node_path.read_text(encoding="utf-8"))
    data["summary"] = "tampered"
    node_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(AssuranceValidationError, match="Digest mismatch"):
        import_assurance_release(release, repo_root=tmp_repo, write=True)


def test_import_lifecycle_rejected(tmp_repo: Path, tmp_path: Path) -> None:
    release = write_release_bundle(tmp_path / "release-life", "action-life")
    man = json.loads((release / "AssuranceReleaseManifest.v1.json").read_text(encoding="utf-8"))
    man["lifecycle"] = "draft"
    (release / "AssuranceReleaseManifest.v1.json").write_text(
        json.dumps(man, indent=2) + "\n", encoding="utf-8"
    )
    with pytest.raises(AssuranceValidationError, match="Lifecycle"):
        import_assurance_release(release, repo_root=tmp_repo, write=True)


def test_import_missing_pcs_pointer(tmp_repo: Path, tmp_path: Path) -> None:
    release = write_release_bundle(tmp_path / "release-pcs", "action-pcs", pcs_mode="claim_pointers")
    man = json.loads((release / "AssuranceReleaseManifest.v1.json").read_text(encoding="utf-8"))
    man["artifacts"]["pcs"] = {
        "mode": "claim_pointers",
        "bundle_path": None,
        "claim_pointers": [
            {"claim_id": "missing-claim", "digest": "sha256:" + ("c" * 64)},
        ],
    }
    (release / "AssuranceReleaseManifest.v1.json").write_text(
        json.dumps(man, indent=2) + "\n", encoding="utf-8"
    )
    with pytest.raises(AssuranceValidationError, match="Missing PCS claim"):
        import_assurance_release(release, repo_root=tmp_repo, write=True)


def test_historical_mutation_rejected(tmp_repo: Path, tmp_path: Path) -> None:
    release = write_release_bundle(tmp_path / "release-mut", "action-mut")
    import_assurance_release(release, repo_root=tmp_repo, write=True)
    node = make_node("action-mut", "source", summary="mutated history")
    node["node_id"] = "node-source"
    with pytest.raises(AssuranceValidationError, match="Historical mutation"):
        append_node(tmp_repo, node)


def test_duplicate_outcome_on_add(tmp_repo: Path, tmp_path: Path) -> None:
    release = write_release_bundle(
        tmp_path / "release-dup", "action-dup", with_outcome=False, with_calibration=False
    )
    import_assurance_release(release, repo_root=tmp_repo, write=True)
    outcome = base_outcome("action-dup", "outcome-x")
    path = tmp_path / "outcome-x.json"
    path.write_text(json.dumps(outcome), encoding="utf-8")
    add_outcome(tmp_repo, path)
    with pytest.raises(AssuranceValidationError, match="Duplicate"):
        add_outcome(tmp_repo, path)


def test_delayed_outcome_flagged_as_gap(tmp_repo: Path, tmp_path: Path) -> None:
    release = write_release_bundle(
        tmp_path / "release-delay", "action-delay", delayed=True, with_calibration=False
    )
    import_assurance_release(release, repo_root=tmp_repo, write=True)
    result = validate_chain(tmp_repo, "action-delay", strict=False)
    assert any(g["gap_id"].startswith("delayed_outcome:") for g in result["gaps"])


def test_replication_appends_new_node(tmp_repo: Path, tmp_path: Path) -> None:
    release = write_release_bundle(tmp_path / "release-rep", "action-rep")
    import_assurance_release(release, repo_root=tmp_repo, write=True)
    before = load_chain(tmp_repo, "action-rep")
    add_replication_node(tmp_repo, "action-rep", replication_id="r1", summary="Replication attempt")
    after = load_chain(tmp_repo, "action-rep")
    assert len(after.nodes) == len(before.nodes) + 1
    assert any(n.get("node_class") == "replication" for n in after.nodes.values())


def test_cycle_rejected(tmp_repo: Path, tmp_path: Path) -> None:
    release = write_release_bundle(
        tmp_path / "release-cyc", "action-cyc", with_outcome=False, with_calibration=False
    )
    import_assurance_release(release, repo_root=tmp_repo, write=True)
    from sm_pipeline.assurance.graph import append_edge

    edge = {
        "schema_version": "v1",
        "edge_id": "edge-cycle",
        "action_id": "action-cyc",
        "from_node_id": "node-verification_result",
        "to_node_id": "node-source",
        "relation": "depends_on",
        "created_at": "2026-07-01T00:00:00Z",
        "notes": None,
    }
    edge["content_digest"] = content_digest(edge, digest_fields=("content_digest",))
    with pytest.raises(AssuranceValidationError, match="Cycle"):
        append_edge(tmp_repo, edge)


def test_metrics_denominator_reconciliation(tmp_repo: Path, tmp_path: Path) -> None:
    release = write_release_bundle(tmp_path / "release-met", "action-met")
    import_assurance_release(release, repo_root=tmp_repo, write=True)
    report = compute_autonomous_science_metrics(tmp_repo)
    pop = len(report["population_action_ids"])
    pop_ids = set(report["population_action_ids"])
    for key, slice_data in report["metrics"].items():
        reconcile_metric_slice(slice_data, pop)
        assert "definition_id" in slice_data
        assert "exclusions" in slice_data
        assert "included_ids" in slice_data
        included = set(slice_data["included_ids"])
        excluded = {e["id"] for e in slice_data["exclusions"]}
        assert included | excluded == pop_ids
        assert not (included & excluded)


def test_import_identity_conflict_node_action_id(tmp_repo: Path, tmp_path: Path) -> None:
    release = write_release_bundle(tmp_path / "release-id", "action-id")
    node_path = release / "nodes" / "node-source.json"
    data = json.loads(node_path.read_text(encoding="utf-8"))
    data["action_id"] = "other-action"
    data["content_digest"] = content_digest(data, digest_fields=("content_digest",))
    node_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    # Refresh checksums for the tampered node and manifest entries
    from sm_pipeline.assurance.hashing import file_sha256

    digest = file_sha256(node_path)
    man = json.loads((release / "AssuranceReleaseManifest.v1.json").read_text(encoding="utf-8"))
    for item in man["artifacts"]["nodes"]:
        if item["path"] == "nodes/node-source.json":
            item["digest"] = digest
    (release / "AssuranceReleaseManifest.v1.json").write_text(
        json.dumps(man, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = []
    for group in (
        man["artifacts"]["execution"],
        man["artifacts"]["outcomes"],
        man["artifacts"]["calibrations"],
        man["artifacts"]["nodes"],
        man["artifacts"]["edges"],
    ):
        for item in group:
            lines.append(f"{item['digest']}  {item['path']}")
    man_path = release / "AssuranceReleaseManifest.v1.json"
    lines.append(f"{file_sha256(man_path)}  AssuranceReleaseManifest.v1.json")
    (release / "checksums.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(AssuranceValidationError, match="action_id conflict"):
        import_assurance_release(release, repo_root=tmp_repo, write=True)


def test_import_partial_release_rejected(tmp_repo: Path, tmp_path: Path) -> None:
    release = write_release_bundle(
        tmp_path / "release-partial",
        "action-partial",
        with_outcome=False,
        with_calibration=False,
    )
    # Remove a required runtime node + its edges from the release
    (release / "nodes" / "node-grant.json").unlink()
    man = json.loads((release / "AssuranceReleaseManifest.v1.json").read_text(encoding="utf-8"))
    man["artifacts"]["nodes"] = [
        item for item in man["artifacts"]["nodes"] if item["path"] != "nodes/node-grant.json"
    ]
    man["artifacts"]["edges"] = [
        item
        for item in man["artifacts"]["edges"]
        if "grant" not in item["path"]
    ]
    from sm_pipeline.assurance.hashing import file_sha256

    (release / "AssuranceReleaseManifest.v1.json").write_text(
        json.dumps(man, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = []
    for group in (
        man["artifacts"]["execution"],
        man["artifacts"]["outcomes"],
        man["artifacts"]["calibrations"],
        man["artifacts"]["nodes"],
        man["artifacts"]["edges"],
    ):
        for item in group:
            # refresh digests from files that remain
            path = release / item["path"]
            item["digest"] = file_sha256(path)
            lines.append(f"{item['digest']}  {item['path']}")
    man_path = release / "AssuranceReleaseManifest.v1.json"
    man_path.write_text(json.dumps(man, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = []
    for group in (
        man["artifacts"]["execution"],
        man["artifacts"]["outcomes"],
        man["artifacts"]["calibrations"],
        man["artifacts"]["nodes"],
        man["artifacts"]["edges"],
    ):
        for item in group:
            lines.append(f"{item['digest']}  {item['path']}")
    lines.append(f"{file_sha256(man_path)}  AssuranceReleaseManifest.v1.json")
    (release / "checksums.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(AssuranceValidationError, match="Partial release"):
        import_assurance_release(release, repo_root=tmp_repo, write=True)


def test_graph_manifest_mutation_rejected(tmp_repo: Path, tmp_path: Path) -> None:
    release = write_release_bundle(tmp_path / "release-gm", "action-gm")
    import_assurance_release(release, repo_root=tmp_repo, write=True)
    node_path = tmp_repo / "corpus" / "assurance" / "actions" / "action-gm" / "nodes" / "node-source.json"
    data = json.loads(node_path.read_text(encoding="utf-8"))
    data["summary"] = "tampered on disk"
    # Write without updating content_digest or graph_manifest — fail closed on validate
    node_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(AssuranceValidationError, match="Historical mutation|digest"):
        validate_chain(tmp_repo, "action-gm")


def test_portal_export_privacy_redaction(tmp_repo: Path, tmp_path: Path) -> None:
    release = write_release_bundle(
        tmp_path / "release-priv", "action-priv", with_outcome=False, with_calibration=False
    )
    import_assurance_release(release, repo_root=tmp_repo, write=True)
    # Add internal node
    node = make_node("action-priv", "review", privacy="internal", summary="secret rationale")
    node["node_id"] = "node-review-internal"
    node["content_digest"] = content_digest(node, digest_fields=("content_digest",))
    append_node(tmp_repo, node)
    export = build_assurance_portal_export(tmp_repo, include_internal=False)
    summaries = [n["summary"] for n in export["actions"]["action-priv"]["nodes"]]
    assert "[redacted]" in summaries
    assert "secret rationale" not in summaries


def test_export_and_reimport(tmp_repo: Path, tmp_path: Path) -> None:
    release = write_release_bundle(tmp_path / "release-ex", "action-ex")
    import_assurance_release(release, repo_root=tmp_repo, write=True)
    before_metrics = compute_autonomous_science_metrics(tmp_repo)
    bundle = tmp_path / "bundle-out"
    export_action_chain(tmp_repo, "action-ex", bundle)
    # Clean-build: empty action store then reimport and validate
    actions = tmp_repo / "corpus" / "assurance" / "actions"
    shutil.rmtree(actions)
    actions.mkdir(parents=True)
    (tmp_repo / "corpus" / "assurance" / "index.json").write_text(
        json.dumps({"schema_version": "v1", "action_ids": []}) + "\n",
        encoding="utf-8",
    )
    report = import_assurance_release(bundle, repo_root=tmp_repo, write=True)
    assert report.ok
    validate_chain(tmp_repo, "action-ex")
    after_metrics = compute_autonomous_science_metrics(tmp_repo)
    for key in before_metrics["metrics"]:
        assert after_metrics["metrics"][key]["numerator"] == before_metrics["metrics"][key]["numerator"]
        assert after_metrics["metrics"][key]["denominator"] == before_metrics["metrics"][key][
            "denominator"
        ]
        reconcile_metric_slice(after_metrics["metrics"][key], len(after_metrics["population_action_ids"]))


def test_add_outcome_does_not_rewrite_pcs_claim(tmp_repo: Path, tmp_path: Path) -> None:
    claim_dir = tmp_repo / "corpus" / "pcs" / "claims" / "claim-frozen"
    claim_dir.mkdir(parents=True)
    claim_doc = {"claim_id": "claim-frozen", "signature_or_digest": "sha256:" + ("d" * 64)}
    claim_path = claim_dir / "read_model.json"
    claim_path.write_text(json.dumps(claim_doc), encoding="utf-8")
    before = claim_path.read_text(encoding="utf-8")

    release = write_release_bundle(
        tmp_path / "release-claim", "action-claim", with_outcome=False, with_calibration=False
    )
    import_assurance_release(release, repo_root=tmp_repo, write=True)
    outcome = base_outcome("action-claim", "outcome-new", pcs_claim_ids=["claim-frozen"])
    opath = tmp_path / "o.json"
    opath.write_text(json.dumps(outcome), encoding="utf-8")
    add_outcome(tmp_repo, opath)
    assert claim_path.read_text(encoding="utf-8") == before


def test_write_portal_export(tmp_repo: Path, tmp_path: Path) -> None:
    release = write_release_bundle(tmp_path / "release-pe", "action-pe")
    import_assurance_release(release, repo_root=tmp_repo, write=True)
    path = write_assurance_portal_export(tmp_repo)
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "action-pe" in data["action_ids"]
