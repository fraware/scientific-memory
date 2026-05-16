"""Ensure pipeline package is importable when running PCS tests from repo root."""

import sys
from pathlib import Path

_PIPELINE_SRC = Path(__file__).resolve().parents[2] / "pipeline" / "src"
if str(_PIPELINE_SRC) not in sys.path:
    sys.path.insert(0, str(_PIPELINE_SRC))
