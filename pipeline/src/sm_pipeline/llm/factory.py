"""Construct the configured LLM provider."""

from __future__ import annotations

from sm_pipeline.llm.prime_intellect import PrimeIntellectProvider
from sm_pipeline.llm.provider import LLMProvider
from sm_pipeline.settings import LLMSettings, load_repo_env


def get_llm_provider(repo_root, *, use_fake: bool = False) -> LLMProvider:
    """Return Prime Intellect provider, or raise if API key missing (unless use_fake)."""
    from pathlib import Path

    root = Path(repo_root).resolve()
    load_repo_env(root)
    settings = LLMSettings.from_env()
    if use_fake:
        from sm_pipeline.llm.provider import FakeLLMProvider

        return FakeLLMProvider()
    return PrimeIntellectProvider(settings)
