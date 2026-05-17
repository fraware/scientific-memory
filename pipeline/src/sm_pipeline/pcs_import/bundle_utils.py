"""Helpers for signed bundle import (SM extensions vs pcs-core envelope)."""

from __future__ import annotations

from typing import Any

SM_EXTENSION_KEYS = frozenset({"reproduce_commands", "verify_commands"})


def bundle_for_validation(bundle: dict[str, Any]) -> dict[str, Any]:
    """Return a copy suitable for pcs-core / strict schema validation."""
    out = dict(bundle)
    for key in SM_EXTENSION_KEYS:
        out.pop(key, None)
    return out
