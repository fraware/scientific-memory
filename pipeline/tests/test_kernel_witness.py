"""Kernel witness policy validation."""

import json
import tempfile
from pathlib import Path

import pytest

from sm_pipeline.validate.kernel_witness import KernelWitnessError, validate_kernel_witness_policy


def test_linked_kernel_must_be_tested() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "corpus").mkdir(parents=True)
        (root / "corpus" / "kernels.json").write_text(
            json.dumps(
                [
                    {
                        "id": "k1",
                        "domain": "x",
                        "io_typing": {
                            "inputs": [{"name": "x", "numeric_kind": "float"}],
                            "outputs": [{"name": "y", "numeric_kind": "float"}],
                        },
                        "semantic_contract": "",
                        "linked_theorem_cards": ["card1"],
                        "test_status": "untested",
                    }
                ]
            ),
            encoding="utf-8",
        )
        with pytest.raises(KernelWitnessError, match="test_status"):
            validate_kernel_witness_policy(root)


def test_linked_kernel_tested_passes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "corpus").mkdir(parents=True)
        (root / "corpus" / "kernels.json").write_text(
            json.dumps(
                [
                    {
                        "id": "k1",
                        "domain": "x",
                        "io_typing": {
                            "inputs": [{"name": "x", "numeric_kind": "float"}],
                            "outputs": [{"name": "y", "numeric_kind": "float"}],
                        },
                        "semantic_contract": "",
                        "linked_theorem_cards": ["card1"],
                        "test_status": "tested",
                    }
                ]
            ),
            encoding="utf-8",
        )
        validate_kernel_witness_policy(root)
