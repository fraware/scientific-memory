"""Mapping generation tests."""

import json
import tempfile
from pathlib import Path

from sm_pipeline.formalize.mapping import generate_mapping


def test_generate_mapping_prefers_linked_formal_targets() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paper = root / "corpus" / "papers" / "p1"
        paper.mkdir(parents=True)
        (paper / "mapping.json").write_text(
            json.dumps(
                {
                    "paper_id": "p1",
                    "namespace": "ScientificMemory.Chemistry.Adsorption.P1",
                    "claim_to_decl": {},
                }
            ),
            encoding="utf-8",
        )
        (paper / "claims.json").write_text(
            json.dumps(
                [
                    {
                        "id": "p1_claim_001",
                        "linked_formal_targets": [
                            "ScientificMemory.Chemistry.Adsorption.P1.my_decl"
                        ],
                    }
                ]
            ),
            encoding="utf-8",
        )
        output = generate_mapping(root, "p1")
        assert output["claim_to_decl"]["p1_claim_001"] == "my_decl"
