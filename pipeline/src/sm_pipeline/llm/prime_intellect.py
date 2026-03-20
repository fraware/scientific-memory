"""Prime Intellect OpenAI-compatible chat completions (https://api.pinference.ai/api/v1)."""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from sm_pipeline.llm.provider import LLMMessage, LLMProvider, LLMResponse
from sm_pipeline.settings import LLMSettings


class PrimeIntellectProvider(LLMProvider):
    def __init__(self, settings: LLMSettings) -> None:
        self._settings = settings

    def complete(
        self,
        messages: list[LLMMessage],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int | None = 2048,
    ) -> LLMResponse:
        api_key = self._settings.require_api_key()
        url = f"{self._settings.base_url}/chat/completions"
        headers: dict[str, str] = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if self._settings.team_id:
            headers["X-Prime-Team-ID"] = self._settings.team_id.strip()

        body: dict[str, Any] = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "stream": False,
        }
        if max_tokens is not None:
            body["max_tokens"] = max_tokens

        last_err: Exception | None = None
        for attempt in range(self._settings.max_retries):
            try:
                with httpx.Client(timeout=self._settings.timeout_seconds) as client:
                    r = client.post(url, headers=headers, json=body)
                if r.status_code == 429:
                    wait = min(2**attempt, 30)
                    time.sleep(wait)
                    continue
                r.raise_for_status()
                data = r.json()
                return _parse_chat_completion(data, model)
            except (httpx.HTTPError, json.JSONDecodeError, KeyError, IndexError) as e:
                last_err = e
                if attempt < self._settings.max_retries - 1:
                    time.sleep(min(2**attempt, 10))
                    continue
                raise RuntimeError(f"Prime Intellect request failed after retries: {e}") from e
        raise RuntimeError(f"Prime Intellect request failed: {last_err}")


def _parse_chat_completion(data: dict[str, Any], requested_model: str) -> LLMResponse:
    choices = data.get("choices") or []
    if not choices:
        raise KeyError("choices")
    msg = choices[0].get("message") or {}
    content = msg.get("content")
    if content is None:
        raise KeyError("message.content")
    usage = data.get("usage") or {}
    return LLMResponse(
        text=str(content).strip(),
        model=str(data.get("model") or requested_model),
        prompt_tokens=_int_or_none(usage.get("prompt_tokens")),
        completion_tokens=_int_or_none(usage.get("completion_tokens")),
        total_tokens=_int_or_none(usage.get("total_tokens")),
        raw_finish_reason=str(choices[0].get("finish_reason") or "") or None,
    )


def _int_or_none(v: Any) -> int | None:
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None
