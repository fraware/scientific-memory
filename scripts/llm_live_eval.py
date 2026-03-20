#!/usr/bin/env python3
"""Optional LLM evaluation run: smoke each proposal surface per paper, write a JSON report.

Uses the pipeline package (same code paths as CLI). Default is ``--use-fake-provider`` so the
script is safe in CI or without API keys. For live runs, omit that flag and set
``PRIME_INTELLECT_API_KEY`` (see docs/prime-intellect-llm.md).

Examples (repo root)::

    uv run python scripts/llm_live_eval.py --paper-ids math_sum_evens --use-fake-provider
    uv run python scripts/llm_live_eval.py --paper-ids math_sum_evens --output benchmarks/reports/llm_live_manual.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "pipeline" / "src"))

from sm_pipeline.llm.factory import get_llm_provider  # noqa: E402
from sm_pipeline.llm.proposals_claims import generate_llm_claim_proposals  # noqa: E402
from sm_pipeline.llm.proposals_lean import generate_llm_lean_proposals  # noqa: E402
from sm_pipeline.llm.proposals_mapping import generate_llm_mapping_proposals  # noqa: E402
from sm_pipeline.models.llm_proposals import (  # noqa: E402
    LlmClaimProposalsBundle,
    LlmLeanProposalsBundle,
    LlmMappingProposalsBundle,
)
from sm_pipeline.settings import LLMSettings, load_repo_env  # noqa: E402


def _validate_claim(data: dict) -> tuple[bool, str | None]:
    try:
        LlmClaimProposalsBundle.model_validate(data)
        return True, None
    except Exception as e:
        return False, str(e)


def _validate_mapping(data: dict) -> tuple[bool, str | None]:
    try:
        LlmMappingProposalsBundle.model_validate(data)
        return True, None
    except Exception as e:
        return False, str(e)


def _validate_lean(data: dict) -> tuple[bool, str | None]:
    try:
        LlmLeanProposalsBundle.model_validate(data)
        return True, None
    except Exception as e:
        return False, str(e)


def _lean_conversion_ready_count(repo_root: Path, data: dict) -> int:
    try:
        b = LlmLeanProposalsBundle.model_validate(data)
    except Exception:
        return 0
    n = 0
    for p in b.proposals:
        tf = (p.target_file or "").strip().replace("\\", "/")
        if not tf.startswith("formal/") or ".." in tf:
            continue
        if not p.replacements:
            continue
        path = repo_root / tf
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        ok = True
        for r in p.replacements:
            if text.count(r.find) != 1:
                ok = False
                break
        if ok:
            n += 1
    return n


def main() -> int:
    p = argparse.ArgumentParser(description="LLM smoke / live eval report per paper.")
    p.add_argument(
        "--paper-ids",
        required=True,
        help="Comma-separated paper ids (corpus/papers/<id>).",
    )
    p.add_argument(
        "--output",
        "-o",
        help="Write JSON report (default: benchmarks/reports/llm_live_<timestamp>.json).",
    )
    p.add_argument(
        "--use-fake-provider",
        action="store_true",
        help="Stub provider; no network.",
    )
    args = p.parse_args()
    repo_root = Path(".").resolve()
    load_repo_env(repo_root)
    settings = LLMSettings.from_env()
    provider = get_llm_provider(repo_root, use_fake=args.use_fake_provider)
    paper_ids = [x.strip() for x in args.paper_ids.split(",") if x.strip()]

    report: dict = {
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "repo_root": str(repo_root),
        "use_fake_provider": args.use_fake_provider,
        "model_claims": settings.model_claims,
        "model_mapping": settings.model_mapping,
        "model_lean": settings.model_lean,
        "papers": [],
    }

    for pid in paper_ids:
        entry: dict = {"paper_id": pid, "surfaces": {}}
        paper_dir = repo_root / "corpus" / "papers" / pid
        if not paper_dir.is_dir():
            entry["error"] = "paper_dir_missing"
            report["papers"].append(entry)
            continue

        try:
            cdata = generate_llm_claim_proposals(
                repo_root, pid, provider, model=settings.model_claims
            )
            ok, err = _validate_claim(cdata)
            entry["surfaces"]["claims"] = {
                "ok": ok,
                "error": err,
                "proposal_count": len(cdata.get("proposals") or []),
                "metadata": cdata.get("metadata"),
            }
        except Exception as e:
            entry["surfaces"]["claims"] = {"ok": False, "error": str(e)}

        if (paper_dir / "mapping.json").is_file():
            try:
                mdata = generate_llm_mapping_proposals(
                    repo_root, pid, provider, model=settings.model_mapping
                )
                ok, err = _validate_mapping(mdata)
                entry["surfaces"]["mapping"] = {
                    "ok": ok,
                    "error": err,
                    "proposal_count": len(mdata.get("proposals") or []),
                    "metadata": mdata.get("metadata"),
                }
            except Exception as e:
                entry["surfaces"]["mapping"] = {"ok": False, "error": str(e)}
        else:
            entry["surfaces"]["mapping"] = {"skipped": True, "reason": "no mapping.json"}

        if (paper_dir / "mapping.json").is_file():
            try:
                ldata = generate_llm_lean_proposals(
                    repo_root, pid, provider, model=settings.model_lean
                )
                ok, err = _validate_lean(ldata)
                entry["surfaces"]["lean"] = {
                    "ok": ok,
                    "error": err,
                    "proposal_count": len(ldata.get("proposals") or []),
                    "conversion_ready_static": _lean_conversion_ready_count(repo_root, ldata),
                    "metadata": ldata.get("metadata"),
                }
            except Exception as e:
                err = str(e)
                # Provider routing can differ by model; if Lean model 404s, retry once with
                # mapping model to keep live eval actionable without mutating repo settings.
                if (
                    "404" in err
                    and settings.model_mapping
                    and settings.model_mapping != settings.model_lean
                ):
                    try:
                        ldata = generate_llm_lean_proposals(
                            repo_root, pid, provider, model=settings.model_mapping
                        )
                        ok, err2 = _validate_lean(ldata)
                        entry["surfaces"]["lean"] = {
                            "ok": ok,
                            "error": err2,
                            "proposal_count": len(ldata.get("proposals") or []),
                            "conversion_ready_static": _lean_conversion_ready_count(repo_root, ldata),
                            "metadata": ldata.get("metadata"),
                            "fallback_model_used": settings.model_mapping,
                            "fallback_reason": "primary_model_404",
                        }
                    except Exception as e2:
                        entry["surfaces"]["lean"] = {
                            "ok": False,
                            "error": str(e2),
                            "fallback_model_used": settings.model_mapping,
                            "fallback_reason": "primary_model_404",
                        }
                else:
                    entry["surfaces"]["lean"] = {"ok": False, "error": err}
        else:
            entry["surfaces"]["lean"] = {"skipped": True, "reason": "no mapping.json"}

        report["papers"].append(entry)

    out_path = Path(args.output) if args.output else None
    if out_path is None:
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        out_path = repo_root / "benchmarks" / "reports" / f"llm_live_{ts}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
