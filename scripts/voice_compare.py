"""Same text, several voice engines, side by side (founder 2026-11-19: HeyGen's Arabic was not good enough).

    python scripts/voice_compare.py lab/ar_mix_w45_part1.txt out_dir

HeyGen (the current Arabic clone) and, when ELEVENLABS_API_KEY is set, ElevenLabs with the founder's own voice:
ELEVENLABS_VOICE_ID if set, otherwise an instant clone made from his own recording
(reviewed/2026-W45/narration.m4a, the founder's read of W45) and kept for later runs. ElevenLabs is tried
with two models. Each engine writes <engine>.mp3; a missing key skips that engine and says so."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
EL = "https://api.elevenlabs.io/v1"


def heygen(text: str, dest: Path) -> str:
    key = os.environ.get("HEYGEN_API_KEY")
    if not key:
        return "HeyGen: no HEYGEN_API_KEY"
    r = requests.post("https://api.heygen.com/v3/models/audio/tts", timeout=300, headers={"X-Api-Key": key},
                      json={"text": text, "voice_id": "4c810d9c9906445f81dfd4f7d32259e0", "language": "ar"})
    if r.status_code >= 400:
        return f"HeyGen: HTTP {r.status_code} {r.text[:200]}"
    url = r.json()["data"]["audio_url"]
    wav = dest.with_suffix(".wav")
    wav.write_bytes(requests.get(url, timeout=300).content)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav), "-b:a", "128k", str(dest)], check=True)
    wav.unlink()
    return f"HeyGen: {dest.name}"


def el_voice(key: str) -> str:
    vid = os.environ.get("ELEVENLABS_VOICE_ID", "").strip()
    if vid:
        return vid
    src = ROOT / "reviewed" / "2026-W45" / "narration.m4a"
    sample = Path("clone_sample.mp3")   # 2 minutes of the founder's read, mono
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "20", "-t", "120", "-i", str(src), "-ac", "1",
                    "-b:a", "128k", str(sample)], check=True)
    with open(sample, "rb") as f:
        r = requests.post(f"{EL}/voices/add", timeout=300, headers={"xi-api-key": key},
                          data={"name": "Wissam (AI This Week)", "description": "The founder's own voice, from his W45 read"},
                          files={"files": (sample.name, f, "audio/mpeg")})
    r.raise_for_status()
    vid = r.json()["voice_id"]
    try:   # keep it for later runs and the pipeline (needs SECRETS_PAT, like the other platforms)
        sys.path.insert(0, str(ROOT))
        from pipeline.publish.social import store_secret
        saved = store_secret("ELEVENLABS_VOICE_ID", vid)
    except Exception:  # noqa: BLE001
        saved = False
    print(f"ElevenLabs: made voice {vid} from the founder's W45 read"
          + ("; saved as the ELEVENLABS_VOICE_ID secret" if saved else ". Save it as the ELEVENLABS_VOICE_ID secret."))
    return vid


def elevenlabs(text: str, out: Path) -> list[str]:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        return ["ElevenLabs: no ELEVENLABS_API_KEY secret, skipped"]
    try:
        vid = el_voice(key)
    except requests.RequestException as exc:
        return [f"ElevenLabs: voice not made: {exc}"]
    lines = []
    for model in ("eleven_multilingual_v2", "eleven_v3"):
        r = requests.post(f"{EL}/text-to-speech/{vid}", timeout=300,
                          headers={"xi-api-key": key, "Accept": "audio/mpeg"},
                          json={"text": text, "model_id": model, "language_code": "ar",
                                "voice_settings": {"stability": 0.5, "similarity_boost": 0.85, "style": 0.15,
                                                   "use_speaker_boost": True}})
        if r.status_code >= 400:
            lines.append(f"ElevenLabs {model}: HTTP {r.status_code} {r.text[:200]}")
            continue
        (out / f"elevenlabs_{model}.mp3").write_bytes(r.content)
        lines.append(f"ElevenLabs {model}: elevenlabs_{model}.mp3")
    return lines


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    from pipeline.script_format import speakable   # the same name fixes the pipeline's voice uses
    text = speakable(Path(sys.argv[1]).read_text(encoding="utf-8").strip())
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    report = [heygen(text, out / "heygen.mp3"), *elevenlabs(text, out)]
    print("\n".join(report))
    (out / "report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
