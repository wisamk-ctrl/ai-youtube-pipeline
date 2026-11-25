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
import re
import time
from pathlib import Path
from typing import Any, Callable

import requests

log = logging.getLogger(__name__)
URL = "https://api.heygen.com/v3/models/audio/tts"


def speak(text: str, voice_id: str, language: str, key: str, model: str = "heygen-voice-1",
          http=requests, sleep: Callable[[float], None] = time.sleep, tries: int = 5,
          opts: dict[str, Any] | None = None) -> tuple[str, float]:
    """(audio URL, seconds) for `text` in the cloned voice. `opts` adds delivery fields to the body
    (speed 0.75-1.25, pitch_variance 0.5-2, expressiveness_boost 0-1)."""
    body = {"voice_id": voice_id, "text": text, "language": language, "model": model, **(opts or {})}
    wait = 5.0
    for n in range(1, tries + 1):
        r = http.post(URL, json=body, timeout=300, headers={"X-Api-Key": key, "Content-Type": "application/json"})
        if r.status_code == 200:
            data = r.json().get("data") or {}
            if not data.get("audio_url"):
                raise RuntimeError(f"HeyGen speech: no audio_url in the answer: {str(r.text)[:300]}")
            return str(data["audio_url"]), float(data.get("duration") or 0.0)
        if r.status_code == 400 and "break tags are not supported" in str(r.text) and "<break" in body["text"]:
            # Instant voice clones refuse SSML breaks (W47-en, 2026-11-20): say the pauses as "..." instead.
            log.warning("HeyGen speech: this voice takes no break tags; sending the pauses as '...'")
            body["text"] = re.sub(r'\s*<break time="[\d.]+s"/>\s*', " ... ", body["text"])
            continue
        if r.status_code in (429, 500, 502, 503, 504) and n < tries:
            delay = float(r.headers.get("Retry-After") or wait)
            log.warning("HeyGen speech: HTTP %s, retrying in %.0f s (%d/%d)", r.status_code, delay, n, tries)
            sleep(delay)
            wait *= 2
            continue
        raise RuntimeError(f"HeyGen speech: HTTP {r.status_code}: {str(r.text)[:300]}")
    raise RuntimeError("HeyGen speech: no answer")


TAG_SPAN = 200   # HeyGen: an emotion tag colours about 233 characters of speech after it, so it is repeated


def styled(text: str, style: dict[str, Any] | None) -> str:
    """`text` with the style's audio tag (e.g. "excited") at its start and again at the first sentence
    break after every TAG_SPAN characters. Instant voices perform the tag; it is not spoken."""
    tag = (style or {}).get("tag")
    if not tag:
        return text
    out, run = [], 0
    for s in re.split(r"(?<=[.!?؟])\s+", text.strip()):
        if not out or run >= TAG_SPAN:
            out.append(f"[{tag}] {s}")
            run = 0
        else:
            out.append(s)
        run += len(s) + 1
    return " ".join(out)


def speech_opts(style: dict[str, Any] | None) -> dict[str, Any]:
    return {k: v for k, v in (style or {}).items() if k in ("speed", "pitch_variance", "pitch_shift", "expressiveness_boost")}


def text_sha(text: str, style: dict[str, Any] | None = None) -> str:
    import hashlib
    key = " ".join(text.split()) + (repr(sorted(style.items())) if style else "")
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def is_current(path: Path, chunks: list[dict[str, Any]], style: dict[str, Any] | None = None) -> bool:
    """An automatic voice.yaml still matches the chunks: same ids, each voiced from the same text. A restored
    run whose script changed afterwards must be voiced again (2026-11-18: the California Short kept its old voice)."""
    import yaml
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return False
    return (isinstance(data, dict) and set(data) == {c["id"] for c in chunks}
            and all(isinstance(data[c["id"]], dict) and data[c["id"]].get("text_sha") == text_sha(c["text"], style)
                    for c in chunks))


def voice_week(chunks: list[dict[str, Any]], cfg: dict[str, Any], dest: Path, key: str | None = None,
               speak_fn: Callable[..., tuple[str, float]] = speak, style: dict[str, Any] | None = None) -> Path:
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
        extra = {"opts": speech_opts(style)} if speech_opts(style) else {}
        url, secs = speak_fn(styled(c["text"], style), voice, "en" if en else "ar", key, model, **extra)
        log.info("Voiced %s: %.1f s", c["id"], secs)
        out[c["id"]] = {"audio": url, "duration": round(secs, 3), "text_sha": text_sha(c["text"], style)}
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("# Voiced automatically through the HeyGen API (pipeline/video/tts.py).\n"
                    + yaml.safe_dump(out, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return dest
