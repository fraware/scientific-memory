"""Research-value metric: disputed claims with linked formal targets."""

import json
from pathlib import Path

from sm_pipeline.metrics.research_value import compute_research_value_metrics


def test_disputed_claims_with_formal_targets_counts(tmp_path: Path) -> None:
    root = tmp_path
    (root / "corpus").mkdir()
    (root / "corpus" / "papers").mkdir()
    (root / "corpus" / "index.json").write_text(
        json.dumps({"version": "0.1", "papers": [{"id": "p1"}, {"id": "p2"}]}),
        encoding="utf-8",
    )
    claims_p1 = [
        {
            "id": "c1",
            "status": "disputed",
            "linked_formal_targets": ["Some.Namespace.decl"],
        },
        {"id": "c2", "status": "disputed", "linked_formal_targets": []},
        {"id": "c3", "status": "machine_checked", "linked_formal_targets": ["X.y"]},
    ]
    (root / "corpus" / "papers" / "p1").mkdir()
    (root / "corpus" / "papers" / "p1" / "claims.json").write_text(
        json.dumps(claims_p1), encoding="utf-8"
    )
    (root / "corpus" / "papers" / "p2").mkdir()
    (root / "corpus" / "papers" / "p2" / "claims.json").write_text(
        json.dumps(
            [
                {
                    "id": "c4",
                    "status": "disputed",
                    "linked_formal_targets": ["A.b", "A.c"],
                }
            ]
        ),
        encoding="utf-8",
    )

    m = compute_research_value_metrics(root)
    assert m["disputed_claims_with_formal_targets"] == 2
