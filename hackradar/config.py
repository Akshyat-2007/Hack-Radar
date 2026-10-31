"""Config: loads .env and exposes provider selection + API keys."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root or package dir
_root_env = Path(__file__).resolve().parent.parent / ".env"
_pkg_env = Path(__file__).resolve().parent / ".env"
if _root_env.exists():
    load_dotenv(_root_env, override=False)
elif _pkg_env.exists():
    load_dotenv(_pkg_env, override=False)
else:
    load_dotenv(override=False)


def _bool(name: str, default: bool = True) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    """Application settings, mostly used by the real provider stubs."""

    def __init__(self) -> None:
        self.use_mocks: bool = _bool("USE_MOCKS", default=False)
        self.tinyfish_api_key: str = os.environ.get("TINYFISH_API_KEY", "")
        self.search_api_key: str = os.environ.get("SEARCH_API_KEY") or self.tinyfish_api_key
        self.fetch_api_key: str = os.environ.get("FETCH_API_KEY") or self.tinyfish_api_key
        self.agent_api_key: str = os.environ.get("AGENT_API_KEY") or self.tinyfish_api_key

        self.gemini_api_key: str = os.environ.get("GEMINI_API_KEY", "")
        self.llm_api_key: str = os.environ.get("LLM_API_KEY") or self.gemini_api_key
        self.llm_model: str = os.environ.get("LLM_MODEL", "gemini-flash-lite-latest")

        self.search_endpoint: str = os.environ.get("SEARCH_ENDPOINT", "https://api.search.tinyfish.ai")
        self.fetch_endpoint: str = os.environ.get("FETCH_ENDPOINT", "https://api.fetch.tinyfish.ai")
        self.agent_endpoint: str = os.environ.get("AGENT_ENDPOINT", "https://agent.tinyfish.ai/v1/automation/run")
        self.llm_endpoint: str = os.environ.get("LLM_ENDPOINT", "https://generativelanguage.googleapis.com/v1beta")


settings = Settings()


def is_mock_mode() -> bool:
    return settings.use_mocks


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent