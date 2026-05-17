"""Canonical JSON hashing (pcs-core compatible; pcs-core remains canonical)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SIGNATURE_FIELD = "signature_or_digest"


def _sort_keys(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _sort_keys(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_sort_keys(item) for item in value]
    return value


def canonicalize_for_hash(data: dict[str, Any]) -> dict[str, Any]:
    payload = dict(data)
    payload.pop(SIGNATURE_FIELD, None)
    sorted_payload = _sort_keys(payload)
    assert isinstance(sorted_payload, dict)
    return sorted_payload


def canonical_hash(data: dict[str, Any]) -> str:
    canonical = canonicalize_for_hash(data)
    digest = hashlib.sha256(
        json.dumps(canonical, separators=(",", ":"), ensure_ascii=False).encode("utf-8"),
    ).hexdigest()
    return f"sha256:{digest}"


def file_sha256_digest(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"
