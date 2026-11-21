"""Sound effects from ElevenLabs for the section cuts (founder 2026-11-21).

Generated once (scripts/make_sfx.py, run by .github/workflows/sfx.yml with ELEVENLABS_API_KEY), levelled to the
synthesised whoosh's loudness and committed under assets/sfx/. The final mix (audio.master) rotates them across
the cuts; with none committed it falls back to the synthesised whoosh. Our own generated sound, never licensed.
"""
from __future__ import annotations

import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Any

import numpy as np
import requests

API = "https://api.elevenlabs.io/v1/sound-generation"


def _read(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(float) / 32767
        return pcm.reshape(-1, w.getnchannels())


def rms(path: Path) -> float:
    return float(np.sqrt(np.mean(_read(path) ** 2)))


def _levelled(src: Path, dest: Path) -> Path:
    """Any audio file → 48 kHz stereo wav at the whoosh's level (too short for loudnorm to measure)."""
    from pipeline.post import audio
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw.wav"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-ac", "2", "-ar", str(audio.RATE),
                        "-c:a", "pcm_s16le", str(raw)], check=True)
        x = _read(raw)
    x *= audio.WHOOSH_RMS / max(1e-9, float(np.sqrt(np.mean(x ** 2))))
    return audio._write_wav(dest, x)


def generate(items: list[dict[str, Any]], out_dir: Path, key: str, http=requests) -> list[Path]:
    """Each `{name, prompt, seconds}` as out_dir/<name>.wav; sounds already there are kept, not re-bought."""
    out_dir.mkdir(parents=True, exist_ok=True)
    done = []
    for it in items:
        dest = out_dir / f"{it['name']}.wav"
        if not dest.exists():
            r = http.post(API, json={"text": it["prompt"], "duration_seconds": float(it.get("seconds", 1.0)),
                                     "prompt_influence": float(it.get("influence", 0.5))},
                          headers={"xi-api-key": key, "accept": "audio/mpeg"}, timeout=120)
            r.raise_for_status()
            with tempfile.TemporaryDirectory() as tmp:
                mp3 = Path(tmp) / "sfx.mp3"
                mp3.write_bytes(r.content)
                _levelled(mp3, dest)
        done.append(dest)
    return done


def cut_sounds(sfx_dir: Path, work: Path) -> list[Path]:
    """The sounds for the section cuts, in rotation order: the committed set, else the synthesised whoosh."""
    files = sorted(sfx_dir.glob("*.wav")) if sfx_dir.is_dir() else []
    if files:
        return files
    from pipeline.post import audio
    return [audio.whoosh(work / "whoosh.wav")]
