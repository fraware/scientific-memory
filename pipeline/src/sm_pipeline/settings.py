"""Pipeline settings: env-based config including Prime Intellect (optional LLM)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # type: ignore[misc, assignment]


def load_repo_env(repo_root: Path) -> None:
    """Load root `.env` into the process environment (does not override existing vars)."""
    env_path = repo_root.resolve() / ".env"
    if load_dotenv is not None:
        load_dotenv(env_path, override=False)
    elif env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val


@dataclass(frozen=True)
class LLMSettings:
    """Prime Intellect inference API (OpenAI-compatible chat completions)."""

    api_key: str | None
    base_url: str
    team_id: str | None
    default_model: str
    model_claims: str
    model_mapping: str
    model_lean: str
    timeout_seconds: float
    max_retries: int

    @classmethod
    def from_env(cls) -> LLMSettings:
        return cls(
            api_key=os.getenv("PRIME_INTELLECT_API_KEY") or os.getenv("SM_PRIME_INTELLECT_API_KEY"),
            base_url=(
                os.getenv("PRIME_INTELLECT_BASE_URL") or "https://api.pinference.ai/api/v1"
            ).rstrip("/"),
            team_id=os.getenv("PRIME_INTELLECT_TEAM_ID"),
            default_model=os.getenv("SM_LLM_MODEL_DEFAULT") or "meta-llama/llama-3.1-70b-instruct",
            model_claims=os.getenv("SM_LLM_MODEL_CLAIMS")
            or os.getenv("SM_LLM_MODEL_DEFAULT")
            or "meta-llama/llama-3.1-70b-instruct",
            model_mapping=os.getenv("SM_LLM_MODEL_MAPPING")
            or os.getenv("SM_LLM_MODEL_DEFAULT")
            or "meta-llama/llama-3.1-70b-instruct",
            model_lean=os.getenv("SM_LLM_MODEL_LEAN")
            or os.getenv("SM_LLM_MODEL_DEFAULT")
            or "meta-llama/llama-3.1-70b-instruct",
            timeout_seconds=float(os.getenv("SM_LLM_TIMEOUT_SECONDS") or "120"),
            max_retries=int(os.getenv("SM_LLM_MAX_RETRIES") or "3"),
        )

    def require_api_key(self) -> str:
        if not self.api_key or not self.api_key.strip():
            raise RuntimeError(
                "Missing API key: set PRIME_INTELLECT_API_KEY (or SM_PRIME_INTELLECT_API_KEY) "
                "in the environment or in a root `.env` file."
            )
        return self.api_key.strip()
