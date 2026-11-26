"""What is left on each paid service the episodes use, without spending any of it (founder 2026-11-26).

    python scripts/quota.py

ElevenLabs: characters used and left this period. HeyGen API: the API balance (separate from the web app's plan
credits, which the HeyGen connector reports). Anthropic has no balance endpoint: its usage is on the console."""
from __future__ import annotations

import os
from datetime import datetime, timezone

import requests


def elevenlabs() -> str:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        return "ElevenLabs: no key"
    d = requests.get("https://api.elevenlabs.io/v1/user/subscription", timeout=60, headers={"xi-api-key": key}).json()
    if "character_count" not in d:
        return f"ElevenLabs: could not read the subscription ({str(d)[:200]})"
    used, limit = int(d["character_count"]), int(d["character_limit"])
    reset = d.get("next_character_count_reset_unix")
    when = datetime.fromtimestamp(reset, timezone.utc).strftime("%Y-%m-%d") if reset else "?"
    return (f"ElevenLabs ({d.get('tier', '?')}): {used:,} of {limit:,} characters used, {limit - used:,} left, "
            f"resets {when}; professional voice clones allowed: {d.get('professional_voice_limit', '?')}")


def heygen_api() -> str:
    key = os.environ.get("HEYGEN_API_KEY")
    if not key:
        return "HeyGen API: no key"
    r = requests.get("https://api.heygen.com/v2/user/remaining_quota", timeout=60, headers={"X-Api-Key": key})
    try:
        d = r.json().get("data") or {}
    except ValueError:
        return f"HeyGen API: HTTP {r.status_code}"
    return f"HeyGen API balance: {d.get('remaining_quota', '?')} (API units; the web plan's credits are separate)"


if __name__ == "__main__":
    for line in (elevenlabs(), heygen_api()):
        print(line)
