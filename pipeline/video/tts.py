"""Speech straight from HeyGen's API, so the voice step runs without anyone in the loop (founder 2026-11-18:
breaking-news Shorts go out within a couple of hours; until now each chunk was voiced by hand through the
HeyGen connector).

POST https://api.heygen.com/v3/models/audio/tts   (X-Api-Key)
    {"voice_id", "text", "language", "model"}  →  {"data": {"audio_url", "duration"}}
The request stays open until the audio is ready. 30 requests a minute per member; HTTP 429 and 5xx are
retried with backoff (following Retry-After when sent)."""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Callable

import requests

log = logging.getLogger(__name__)
URL = "https://api.heygen.com/v3/models/audio/tts"


def speak(text: str, voice_id: str, language: str, key: str, model: str = "heygen-voice-1",
          http=requests, sleep: Callable[[float], None] = time.sleep, tries: int = 5) -> tuple[str, float]:
    """(audio URL, seconds) for `text` in the cloned voice."""
    body = {"voice_id": voice_id, "text": text, "language": language, "model": model}
    wait = 5.0
    for n in range(1, tries + 1):
        r = http.post(URL, json=body, timeout=300, headers={"X-Api-Key": key, "Content-Type": "application/json"})
        if r.status_code == 200:
            data = r.json().get("data") or {}
            if not data.get("audio_url"):
                raise RuntimeError(f"HeyGen speech: no audio_url in the answer: {str(r.text)[:300]}")
            return str(data["audio_url"]), float(data.get("duration") or 0.0)
        if r.status_code in (429, 500, 502, 503, 504) and n < tries:
            delay = float(r.headers.get("Retry-After") or wait)
            log.warning("HeyGen speech: HTTP %s, retrying in %.0f s (%d/%d)", r.status_code, delay, n, tries)
            sleep(delay)
            wait *= 2
            continue
        raise RuntimeError(f"HeyGen speech: HTTP {r.status_code}: {str(r.text)[:300]}")
    raise RuntimeError("HeyGen speech: no answer")


def voice_week(chunks: list[dict[str, Any]], cfg: dict[str, Any], dest: Path, key: str | None = None,
               speak_fn: Callable[..., tuple[str, float]] = speak) -> Path:
    """Voice every chunk of the pack and write voice.yaml (chunk id → audio link). A face chunk is voiced
    too and stays narration (no presenter video is made automatically)."""
    import yaml
    key = key or os.environ.get("HEYGEN_API_KEY", "")
    if not key:
        raise RuntimeError("HEYGEN_API_KEY is not set: the voice step cannot run on its own")
    h = cfg["video"]["heygen"]
    en = cfg.get("language") == "en"
    voice = (os.environ.get("HEYGEN_VOICE_ID_EN") or h.get("voice_id_en")) if en else (os.environ.get("HEYGEN_VOICE_ID") or h.get("voice_id"))
    if not voice:
        raise RuntimeError("no voice id for this language in video.heygen")
    model = str(h.get("tts_model", "heygen-voice-1"))
    out: dict[str, Any] = {}
    for c in chunks:
        url, secs = speak_fn(c["text"], voice, "en" if en else "ar", key, model)
        log.info("Voiced %s: %.1f s", c["id"], secs)
        out[c["id"]] = {"audio": url, "duration": round(secs, 3)}
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("# Voiced automatically through the HeyGen API (pipeline/video/tts.py).\n"
                    + yaml.safe_dump(out, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return dest
