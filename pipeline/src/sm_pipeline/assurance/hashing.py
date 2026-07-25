"""Content digests for assurance artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

INTEGRITY_DIGEST_FIELD = "content_digest"
ENVELOPE_KEY = "integrity"


def _sort_keys(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _sort_keys(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_sort_keys(item) for item in value]
    return value


def canonicalize_for_digest(data: dict[str, Any], *, digest_fields: tuple[str, ...] = ()) -> dict[str, Any]:
    payload = dict(data)
    for field in digest_fields:
        payload.pop(field, None)
    if ENVELOPE_KEY in payload and isinstance(payload[ENVELOPE_KEY], dict):
        envelope = dict(payload[ENVELOPE_KEY])
        envelope.pop(INTEGRITY_DIGEST_FIELD, None)
        payload[ENVELOPE_KEY] = envelope
    sorted_payload = _sort_keys(payload)
    assert isinstance(sorted_payload, dict)
    return sorted_payload


def content_digest(data: dict[str, Any], *, digest_fields: tuple[str, ...] = (INTEGRITY_DIGEST_FIELD,)) -> str:
    canonical = canonicalize_for_digest(data, digest_fields=digest_fields)
    digest = hashlib.sha256(
        json.dumps(canonical, separators=(",", ":"), ensure_ascii=False).encode("utf-8"),
    ).hexdigest()
    return f"sha256:{digest}"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def normalize_digest(value: str) -> str:
    value = value.strip().lower()
    if value.startswith("sha256:"):
        return value
    if len(value) == 64 and all(c in "0123456789abcdef" for c in value):
        return f"sha256:{value}"
    return value
