"""Narration from ElevenLabs, as the voice-first route's automatic voice step (founder 2026-11-26: "let's also use
ElevenLabs, we have credits there"). The same voice.yaml as pipeline/video/tts.py: one entry per voice-pack chunk with
a public audio link, its length, the word timings and the text it was voiced from; HeyGen then makes only the face
clips, from that audio. Chosen with video.voice_provider: elevenlabs; off by default.

POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps  (xi-api-key)
    {"text", "model_id", "voice_settings"} → {"audio_base64", "alignment": {characters, character_start_times_seconds,
    character_end_times_seconds}}
The audio is published on a GitHub release of this repository (tag voice-<week>) so that the assemble step and
HeyGen's face clips can fetch it by URL. Costs one ElevenLabs character per character of text."""
from __future__ import annotations

import base64
import logging
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

import requests

from pipeline.video.tts import text_sha

log = logging.getLogger(__name__)
API = "https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps"
_BREAK = re.compile(r'<break time="([\d.]+)s"\s*/>')


def ssml_breaks(text: str, longest: float = 3.0) -> str:
    """The pack's pauses in the form ElevenLabs reads (it caps a break at 3 s)."""
    return _BREAK.sub(lambda m: f'<break time="{min(float(m[1]), longest):.1f}s" />', text)


def words_from_alignment(al: dict[str, Any]) -> list[dict[str, Any]]:
    """Character timings → [{word, start, end}], spaces and break tags dropped."""
    chars = al.get("characters") or []
    starts = al.get("character_start_times_seconds") or []
    ends = al.get("character_end_times_seconds") or []
    out, cur, a, b = [], "", None, None
    for ch, s, e in zip(chars, starts, ends):
        if ch.isspace():
            if cur:
                out.append({"word": cur, "start": round(a, 3), "end": round(b, 3)})
            cur, a = "", None
            continue
        if a is None:
            a = float(s)
        cur, b = cur + ch, float(e)
    if cur:
        out.append({"word": cur, "start": round(a, 3), "end": round(b, 3)})
    return [w for w in out if not w["word"].startswith("<") and "time=" not in w["word"] and w["word"] != "/>"]


def speak(text: str, voice_id: str, key: str, settings: dict[str, Any], http=requests,
          sleep: Callable[[float], None] = time.sleep, tries: int = 5) -> tuple[bytes, float, list[dict[str, Any]]]:
    """(mp3 bytes, seconds, words) for `text` in the given voice."""
    body = {"text": ssml_breaks(text), "model_id": settings.get("model_id", "eleven_multilingual_v2"),
            "voice_settings": {k: settings[k] for k in ("stability", "similarity_boost", "style", "use_speaker_boost",
                                                         "speed") if k in settings}}
    wait = 5.0
    for n in range(1, tries + 1):
        r = http.post(API.format(voice=voice_id), json=body, timeout=300,
                      headers={"xi-api-key": key, "Content-Type": "application/json"})
        if r.status_code == 200:
            d = r.json()
            words = words_from_alignment(d.get("alignment") or {})
            ends = (d.get("alignment") or {}).get("character_end_times_seconds") or [0.0]
            return base64.b64decode(d["audio_base64"]), float(ends[-1]), words
        if r.status_code in (429, 500, 502, 503, 504) and n < tries:
            sleep(float(r.headers.get("Retry-After") or wait))
            wait *= 2
            continue
        raise RuntimeError(f"ElevenLabs speech: HTTP {r.status_code}: {str(r.text)[:300]}")
    raise RuntimeError("ElevenLabs speech: no answer")


def publish(files: list[Path], tag: str, repo: str | None = None, run=subprocess.run) -> dict[str, str]:
    """Uploads the files to the release `tag` (created if missing); file name → public download URL."""
    repo = repo or os.environ.get("GITHUB_REPOSITORY", "wisamk-ctrl/ai-youtube-pipeline")
    if run(["gh", "release", "view", tag, "--repo", repo], capture_output=True).returncode != 0:
        run(["gh", "release", "create", tag, "--repo", repo, "--title", tag, "--prerelease",
             "--notes", "Narration audio for the voice-first render (pipeline/video/eleven_tts.py)."], check=True)
    run(["gh", "release", "upload", tag, "--repo", repo, "--clobber", *map(str, files)], check=True)
    return {f.name: f"https://github.com/{repo}/releases/download/{tag}/{f.name}" for f in files}


def voice_week(chunks: list[dict[str, Any]], cfg: dict[str, Any], dest: Path, week: str, key: str | None = None,
               speak_fn=speak, publish_fn=publish, style: dict[str, Any] | None = None) -> Path:
    """Voice every chunk with ElevenLabs and write voice.yaml (chunk id → audio link, duration, words, text_sha)."""
    import yaml
    key = key or os.environ.get("ELEVENLABS_API_KEY", "")
    voice = os.environ.get("ELEVENLABS_VOICE_ID") or cfg["video"].get("elevenlabs", {}).get("voice_id", "")
    if not key or not voice:
        raise RuntimeError("ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID are needed for the ElevenLabs voice")
    settings = dict(cfg["video"].get("elevenlabs") or {})
    work = dest.parent / "eleven"
    work.mkdir(parents=True, exist_ok=True)
    made: dict[str, dict[str, Any]] = {}
    files = []
    for c in chunks:
        mp3, secs, words = speak_fn(c["text"], voice, key, settings)
        f = work / f"{week}-{c['id']}-{text_sha(c['text'])[:8]}.mp3"
        f.write_bytes(mp3)
        files.append(f)
        made[c["id"]] = {"file": f.name, "duration": round(secs, 3), "words": words,
                         "text_sha": text_sha(c["text"], style)}   # the same key tts.is_current checks
        log.info("Voiced %s with ElevenLabs: %.1f s, %d words", c["id"], secs, len(words))
    urls = publish_fn(files, f"voice-{week}")
    out = {cid: {"audio": urls[e.pop("file")], **e} for cid, e in made.items()}
    dest.write_text("# Voiced automatically through ElevenLabs (pipeline/video/eleven_tts.py).\n"
                    + yaml.safe_dump(out, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return dest
