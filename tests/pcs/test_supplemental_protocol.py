"""Supplemental protocol artifacts (tool-use workflow readiness)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from sm_pipeline.pcs_import.release_context import enrich_read_model_with_release
from sm_pipeline.pcs_import.supplemental_protocol import load_supplemental_protocol_artifacts

from schema_fixtures import LABTRUST_RELEASE_DIR, copy_pcs_schemas


def test_load_tool_use_trace_from_release_dir(tmp_path: Path) -> None:
    root = tmp_path
    copy_pcs_schemas(root)
    release_dir = root / "release"
    shutil.copytree(LABTRUST_RELEASE_DIR, release_dir)
    trace = {
        "schema_version": "v0",
        "trace_id": "trace-tool-use-demo",
        "workflow_id": "tool_use.safety_v0.1",
        "agent_id": "agent-demo",
        "policy_id": "policy-demo",
        "started_at": "2026-05-01T00:00:00Z",
        "completed_at": "2026-05-01T00:01:00Z",
        "tool_calls": [],
        "trace_hash": "sha256:" + "c" * 64,
        "source_repo": "https://github.com/example/agent-runtime",
        "source_commit": "d" * 40,
        "status": "RuntimeObserved",
    }
    (release_dir / "tool_use_trace.v0.json").write_text(
        json.dumps(trace, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest = json.loads((release_dir / "ReleaseManifest.v0.json").read_text(encoding="utf-8-sig"))
    artifacts = manifest.setdefault("artifacts", {})
    artifacts["tool_use_trace.v0.json"] = {
        "artifact_type": "ToolUseTrace.v0",
        "sha256": "sha256:" + "c" * 64,
        "status": "RuntimeObserved",
    }
    supplemental = load_supplemental_protocol_artifacts(manifest, release_dir)
    tool_traces = [a for a in supplemental if a["artifact_type"] == "ToolUseTrace.v0"]
    assert len(tool_traces) == 1
    assert tool_traces[0]["payload"]["trace_id"] == "trace-tool-use-demo"


def test_enrich_read_model_includes_protocol_artifacts(tmp_path: Path) -> None:
    root = tmp_path
    release_dir = root / "release"
    shutil.copytree(LABTRUST_RELEASE_DIR, release_dir)
    trace_path = release_dir / "tool_use_trace.v0.json"
    trace_path.write_text(
        json.dumps(
            {
                "schema_version": "v0",
                "trace_id": "trace-enrich",
                "workflow_id": "tool_use.safety_v0.1",
                "agent_id": "a",
                "policy_id": "p",
                "started_at": "2026-05-01T00:00:00Z",
                "completed_at": "2026-05-01T00:01:00Z",
                "tool_calls": [],
                "trace_hash": "sha256:" + "e" * 64,
                "source_repo": "https://github.com/example/runtime",
                "source_commit": "f" * 40,
                "status": "RuntimeObserved",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    manifest = json.loads((release_dir / "ReleaseManifest.v0.json").read_text(encoding="utf-8-sig"))
    manifest["artifacts"]["tool_use_trace.v0.json"] = {
        "artifact_type": "ToolUseTrace.v0",
        "sha256": "sha256:" + "e" * 64,
    }
    validation = json.loads(
        (release_dir / "ReleaseChainValidationResult.v0.json").read_text(encoding="utf-8-sig"),
    )
    read_model = {"claim_id": "claim-demo", "schema_version": "v0"}
    enriched = enrich_read_model_with_release(
        read_model,
        manifest=manifest,
        validation=validation,
        manifest_path=release_dir / "ReleaseManifest.v0.json",
        repo_root=root,
        lineage={"claim_id": "claim-demo", "stale": False, "stale_reasons": []},
    )
    trace = enriched.get("tool_use_trace")
    assert isinstance(trace, dict)
    assert trace.get("id") == "trace-enrich"
    assert enriched.get("protocol_artifacts") is None
