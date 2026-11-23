"""Face clips straight from HeyGen's API, so an episode renders with the presenter and no chat session
(founder 2026-11-23). Until now each face clip was made by hand through the HeyGen connector.

POST https://api.heygen.com/v3/videos   {"type": "image", "image": {"type": "url", "url"}, "audio_url", ...}
GET  https://api.heygen.com/v3/videos/{id}  → data.status (pending | processing | completed | failed), data.video_url
GET  https://api.heygen.com/v3/users/me     → data.wallet.remaining_balance (USD, prepaid, apart from the plan credits)

Each clip costs money by the second (measured 2026-11-23: $0.40 for 10.06 s). So: a clip is asked for once (the
Idempotency-Key is the picture and the sound), every finished clip is written to voice.yaml at once, and nothing
is started when the wallet cannot cover the whole episode. `video_url` is a signed link that expires, so a clip
older than `face_link_days` is made again.
"""
from __future__ import annotations

import hashlib
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

import requests

log = logging.getLogger(__name__)
BASE = "https://api.heygen.com"


class WalletShort(RuntimeError):
    """The API wallet cannot cover the episode's face clips: nothing was started."""


def balance(key: str, http=requests) -> float | None:
    """The API wallet in USD, or None when it cannot be read (another billing type, a refused key)."""
    r = http.get(f"{BASE}/v3/users/me", timeout=60, headers={"X-Api-Key": key, "Accept": "application/json"})
    if r.status_code != 200:
        return None
    w = ((r.json() or {}).get("data") or {}).get("wallet") or {}
    return float(w["remaining_balance"]) if w.get("currency") == "usd" and w.get("remaining_balance") is not None else None


def cost(seconds: float, cfg: dict[str, Any]) -> float:
    return seconds * float(cfg["video"]["heygen"].get("face_usd_per_second", 0.04))


def make_face(image_url: str, audio_url: str, key: str, http=requests, sleep: Callable[[float], None] = time.sleep,
              wait_s: int = 1800, every_s: int = 20) -> str:
    """One face clip: the still picture speaking the sound file. Returns the finished clip's link."""
    h = {"X-Api-Key": key, "Accept": "application/json"}
    once = "face-" + hashlib.sha256(f"{image_url}|{audio_url}".encode("utf-8")).hexdigest()[:40]
    r = http.post(f"{BASE}/v3/videos", timeout=120, headers={**h, "Content-Type": "application/json", "Idempotency-Key": once},
                  json={"type": "image", "image": {"type": "url", "url": image_url}, "audio_url": audio_url,
                        "resolution": "1080p", "aspect_ratio": "auto", "title": "AI This Week face clip"})
    if r.status_code != 200:
        raise RuntimeError(f"HeyGen face clip: HTTP {r.status_code}: {str(r.text)[:300]}")
    vid = ((r.json() or {}).get("data") or {}).get("video_id")
    if not vid:
        raise RuntimeError(f"HeyGen face clip: no video_id in the answer: {str(r.text)[:300]}")
    for _ in range(max(1, wait_s // every_s)):
        sleep(every_s)
        g = http.get(f"{BASE}/v3/videos/{vid}", timeout=60, headers=h)
        d = ((g.json() or {}).get("data") or {}) if g.status_code == 200 else {}
        if d.get("status") == "completed" and d.get("video_url"):
            return str(d["video_url"])
        if d.get("status") == "failed":
            raise RuntimeError(f"HeyGen face clip {vid}: failed ({d.get('failure_code')}: {d.get('failure_message')})")
    raise RuntimeError(f"HeyGen face clip {vid}: not ready after {wait_s} s")


def face_week(voice: Path, chunks: list[dict[str, Any]], cfg: dict[str, Any], raw_base: str, key: str | None = None,
              balance_fn: Callable[[str], float | None] = balance, make_fn: Callable[[str, str, str], str] = make_face,
              now: datetime | None = None) -> list[str]:
    """Add a presenter clip to every face chunk of an automatic voice.yaml that has none (or whose link has
    expired). Returns the ids it made. Raises WalletShort before spending when the wallet is too low."""
    import yaml
    key = key or os.environ.get("HEYGEN_API_KEY", "")
    if not key:
        raise RuntimeError("HEYGEN_API_KEY is not set: the face clips cannot be made automatically")
    h = cfg["video"]["heygen"]
    if not h.get("face_image"):
        raise RuntimeError("video.heygen.face_image is not set")
    now = now or datetime.now(timezone.utc)
    oldest = (now - timedelta(days=float(h.get("face_link_days", 5)))).strftime("%Y-%m-%dT%H:%M:%SZ")
    text = voice.read_text(encoding="utf-8")
    data = yaml.safe_load(text) or {}
    todo = [c["id"] for c in chunks if c["role"] == "face" and isinstance(data.get(c["id"]), dict)
            and (not data[c["id"]].get("video") or str(data[c["id"]].get("video_at") or "9") < oldest)]
    if not todo:
        return []
    need = cost(sum(float(data[i].get("duration") or 0) for i in todo), cfg) * float(h.get("face_budget_margin", 1.25))
    have = balance_fn(key)
    if have is not None and have < need:
        raise WalletShort(f"HeyGen's API wallet holds ${have:.2f}; the {len(todo)} face clips need about ${need:.2f}. "
                          "Top it up at app.heygen.com (API), or make the face clips from chat.")
    image = f"{raw_base.rstrip('/')}/{str(h['face_image']).lstrip('/')}"
    head = "".join(line + "\n" for line in text.splitlines() if line.startswith("#"))
    made = []
    for i in todo:
        data[i].update(video=make_fn(image, data[i]["audio"], key), video_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"))
        voice.write_text(head + yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")   # paid: keep it
        made.append(i)
        log.info("Face clip %s made (%.1f s)", i, float(data[i].get("duration") or 0))
    return made
