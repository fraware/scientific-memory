"""Provider-agnostic LLM interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LLMMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    text: str
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    raw_finish_reason: str | None = None


class LLMProvider(Protocol):
    def complete(
        self,
        messages: list[LLMMessage],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int | None = 2048,
    ) -> LLMResponse:
        """Return assistant text (non-streaming)."""
        ...


@dataclass
class FakeLLMProvider:
    """Deterministic stub for tests."""

    reply: str = '{"paper_id": "test", "schema_version": "0.1.0", "verification_boundary": "human_review_only", "proposals": []}'
    model: str = "fake"

    def complete(
        self,
        messages: list[LLMMessage],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int | None = 2048,
    ) -> LLMResponse:
        return LLMResponse(text=self.reply, model=self.model or model)
