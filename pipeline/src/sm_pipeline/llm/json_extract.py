"""Extract a JSON object from model output (raw JSON or fenced code block)."""

from __future__ import annotations

import json
import re


def extract_json_object(text: str) -> dict:
    """Parse the first top-level JSON object from text."""
    s = text.strip()
    # Strip ```json ... ``` or ``` ... ```
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", s, re.IGNORECASE)
    if fence:
        s = fence.group(1).strip()
    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output")
    chunk = s[start : end + 1]
    try:
        data = json.loads(chunk)
    except json.JSONDecodeError:
        # Some providers occasionally emit raw control chars inside JSON strings.
        # strict=False accepts those while preserving object structure validation below.
        data = json.loads(chunk, strict=False)
    if not isinstance(data, dict):
        raise TypeError("Expected JSON object at top level")
    return data
