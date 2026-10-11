"""
Configuration loading.

Two sources, deliberately separated:
  * config/settings.yaml  → tunable, non-secret behaviour (feeds, weights, pacing).
  * .env / environment    → secrets (API keys, avatar/voice IDs).

Keeping secrets out of the YAML means the YAML can be committed and reviewed
while the keys stay local (or in your scheduler's secret store).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

# Project root = the ai-youtube-pipeline/ directory, regardless of the cwd the
# script was launched from (cron jobs often run from $HOME).
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SETTINGS = ROOT / "config" / "settings.yaml"


def load_settings(path: Path | None = None) -> dict[str, Any]:
    """Load .env into the process environment, then parse settings.yaml."""
    load_dotenv(ROOT / ".env")  # no-op if absent; real env vars always win
    with open(path or DEFAULT_SETTINGS, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def require_env(name: str) -> str:
    """Fetch a required secret, failing loudly with an actionable message.

    Failing at startup is far cheaper than discovering a missing key after
    20 minutes of ingestion and a paid LLM call.
    """
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required environment variable {name}. "
            f"Copy .env.example to .env and set it."
        )
    return value
