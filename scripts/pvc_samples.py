"""The founder's ElevenLabs training recordings → analysis → cleaned audio → HeyGen (founder 2026-11-23).

    python scripts/pvc_samples.py analyze          # numbers only, nothing uploaded
    python scripts/pvc_samples.py upload           # also uploads the cleaned clone sample to HeyGen as an asset

The recordings are the founder's own voice. They stay on the runner: only measurements are printed, and the
cleaned sample goes straight to HeyGen's asset store (never to the public repo or previews branch)."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import requests

EL = "https://api.elevenlabs.io/v1"
WORK = Path("pvc_work")


def el(path: str, **kw):
    r = requests.get(f"{EL}{path}", headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]}, timeout=300, **kw)
    if r.status_code >= 400:
        sys.exit(f"ElevenLabs {path}: HTTP {r.status_code} {r.text[:300]}")
    return r


def ff(*args: str) -> str:
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *args], capture_output=True, text=True).stderr


def measure(f: Path) -> dict:
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                               capture_output=True, text=True).stdout.strip() or 0)
    info = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
                           "stream=codec_name,sample_rate,channels,bit_rate", "-of", "json", str(f)],
                          capture_output=True, text=True).stdout
    st = (json.loads(info or "{}").get("streams") or [{}])[0]
    loud = ff("-i", str(f), "-af", "ebur128=peak=true", "-f", "null", "-")
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", loud)
    pk = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", loud)
    stats = ff("-i", str(f), "-af", "astats=metadata=0:reset=0", "-f", "null", "-")
    floor = re.findall(r"Noise floor dB:\s*(-?[\d.inf]+)", stats)
    clip = re.findall(r"Number of samples clipped:\s*(\d+)", stats) or re.findall(r"Peak count:\s*(\d+)", stats)
    sil = re.findall(r"silence_duration: ([\d.]+)", ff("-i", str(f), "-af", "silencedetect=n=-45dB:d=0.7", "-f", "null", "-"))
    return {"seconds": round(dur, 1), "codec": st.get("codec_name"), "rate": st.get("sample_rate"),
            "channels": st.get("channels"), "lufs": float(i[-1]) if i else None, "peak_db": float(pk[-1]) if pk else None,
            "noise_floor_db": floor[-1] if floor else None, "silence_s": round(sum(map(float, sil)), 1)}


def enhance(src: Path, dest: Path) -> None:
    """Gentle, voice-safe clean-up: rumble cut, light noise reduction, de-ess, even level. No heavy processing that
    would teach the clone artefacts."""
    chain = ("highpass=f=70,afftdn=nr=10:nf=-50:tn=1,deesser=i=0.3,"
             "acompressor=threshold=-20dB:ratio=2.5:attack=15:release=200:makeup=2,"
             "silenceremove=stop_periods=-1:stop_duration=0.8:stop_threshold=-45dB,"
             "loudnorm=I=-18:TP=-2:LRA=9")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-af", chain, "-ac", "1", "-ar", "44100",
                    str(dest)], check=True)


def main(mode: str) -> None:
    WORK.mkdir(exist_ok=True)
    voices = el("/voices").json().get("voices", [])
    mine = [v for v in voices if v.get("category") != "premade"]
    print("Voices on the account (not premade):", "; ".join(
        f"{v['name']} [{v.get('category')}, {len(v.get('samples') or [])} rec, "
        f"fine-tuning: {(v.get('fine_tuning') or {}).get('state')}]" for v in mine))
    pick = [v for v in mine if "wissam" in v["name"].lower() and v.get("category") == "professional"] or \
           [v for v in mine if "wissam" in v["name"].lower()]
    if not pick:
        sys.exit("No voice named Wissam found")
    v = el(f"/voices/{pick[0]['voice_id']}").json()
    samples = v.get("samples") or []
    print(f"Voice: {v['name']} ({v.get('category')}), {len(samples)} recording(s)")
    files = []
    for k, s in enumerate(samples, 1):
        f = WORK / f"rec_{k:02d}{Path(s.get('file_name') or 'x.mp3').suffix or '.mp3'}"
        r = requests.get(f"{EL}/voices/{v['voice_id']}/samples/{s['sample_id']}/audio", timeout=300,
                         headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]})
        if r.status_code >= 400:   # professional clones keep their recordings under /voices/pvc/
            r = requests.get(f"{EL}/voices/pvc/{v['voice_id']}/samples/{s['sample_id']}/audio", timeout=300,
                             headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]})
        if r.status_code >= 400:
            print(f"  {k:02d} {s.get('file_name')}: not downloadable (HTTP {r.status_code} {r.text[:150]})")
            continue
        ctype = r.headers.get("content-type", "")
        if "json" in ctype:   # some endpoints answer with a signed link
            url = (r.json() or {}).get("audio_base_64") or (r.json() or {}).get("url")
            print(f"  {k:02d} returned JSON keys: {list((r.json() or {}).keys())}")
            continue
        f.write_bytes(r.content)
        files.append(f)
        print(f"  {k:02d} {s.get('file_name')}: {measure(f)}")
    if not files:
        sys.exit("No recordings could be downloaded")
    total = sum(measure(f)["seconds"] for f in files)
    print(f"Total: {total / 60:.1f} min")
    cleaned = []
    for f in files:
        out = WORK / (f.stem + "_clean.wav")
        enhance(f, out)
        cleaned.append(out)
    lst = WORK / "list.txt"
    lst.write_text("".join(f"file '{c.resolve()}'\n" for c in cleaned))
    full = WORK / "all_clean.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), str(full)], check=True)
    sample = WORK / "wissam_clone_sample.mp3"   # an instant clone wants a few clean minutes, not hours
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "5", "-t", "240", "-i", str(full), "-b:a", "192k", str(sample)],
                   check=True)
    print("Cleaned (all):", measure(full))
    print("Clone sample (4 min):", measure(sample))
    if mode != "upload":
        return
    with open(sample, "rb") as fh:
        r = requests.post("https://api.heygen.com/v3/assets", timeout=600, headers={"X-Api-Key": os.environ["HEYGEN_API_KEY"]},
                          files={"file": (sample.name, fh, "audio/mpeg")})
    print("HeyGen upload:", r.status_code, r.text[:400])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "analyze")
