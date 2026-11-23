"""What HeyGen's API has left and what recent calls cost (workflow heygen-cost). Read-only: nothing is generated.

GET /v3/users/me → billing type and balance; GET /v3/usage → the charge of each recent request. Names, e-mail
addresses and the key are never printed (the repo's logs are public)."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone

import requests

BASE = "https://api.heygen.com"
PRIVATE = ("email", "username", "first_name", "last_name", "name", "user_id", "member_id", "api_key")


def scrub(x):
    if isinstance(x, dict):
        return {k: scrub(v) for k, v in x.items() if k not in PRIVATE}
    return [scrub(v) for v in x] if isinstance(x, list) else x


def main(days: int = 14) -> None:
    key = os.environ.get("HEYGEN_API_KEY", "")
    if not key:
        sys.exit("HEYGEN_API_KEY is not set")
    h = {"X-Api-Key": key, "Accept": "application/json"}
    r = requests.get(f"{BASE}/v3/users/me", headers=h, timeout=60)
    print(f"## Balance (HTTP {r.status_code})")
    print(json.dumps(scrub(r.json().get("data", r.json())), indent=1)[:2000] if r.ok else r.text[:300])
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    for fmt in (lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ"), lambda d: int(d.timestamp())):
        r = requests.get(f"{BASE}/v3/usage", headers=h, timeout=60,
                         params={"start_time": fmt(start), "end_time": fmt(end), "limit": 100})
        if r.ok:
            break
    print(f"\n## Usage, last {days} days (HTTP {r.status_code})")
    print(json.dumps(scrub(r.json()), indent=1)[:12000] if r.ok else r.text[:500])


def balance(h: dict) -> float | None:
    d = requests.get(f"{BASE}/v3/users/me", headers=h, timeout=60).json().get("data", {})
    return (d.get("wallet") or {}).get("remaining_balance")


def face_test(image_url: str, audio_url: str, wait_s: int = 1200) -> None:
    """ONE face clip (Avatar IV, a still image driven by an audio file), to measure its price: the wallet is read
    before and after. Spends money: run only on the founder's word (2026-11-23). Never retried."""
    import time
    import uuid
    key = os.environ.get("HEYGEN_API_KEY", "")
    if not key:
        sys.exit("HEYGEN_API_KEY is not set")
    h = {"X-Api-Key": key, "Accept": "application/json"}
    before = balance(h)
    print(f"Wallet before: {before}")
    r = requests.post(f"{BASE}/v3/videos", timeout=120, headers={**h, "Content-Type": "application/json",
                                                                 "Idempotency-Key": f"face-test-{uuid.uuid4().hex}"},
                      json={"type": "image", "image": {"type": "url", "url": image_url}, "audio_url": audio_url,
                            "resolution": "1080p", "aspect_ratio": "auto", "title": "API price test"})
    if not r.ok:
        sys.exit(f"create → HTTP {r.status_code}: {r.text[:500]}")
    made = r.json().get("data", {})
    vid = made.get("video_id")
    print(f"Created: status {made.get('status')}, resolution {made.get('resolution')}, note {made.get('resolution_note')}")
    d, t0 = {}, time.time()
    while time.time() - t0 < wait_s:
        time.sleep(20)
        d = requests.get(f"{BASE}/v3/videos/{vid}", headers=h, timeout=60).json().get("data", {})
        if d.get("status") in ("completed", "failed"):
            break
    print(f"Result: {d.get('status')} after {time.time() - t0:.0f} s, duration {d.get('duration')} s, "
          f"failure {d.get('failure_code')} {d.get('failure_message')}")
    time.sleep(30)   # the charge may post a little after the render
    after = balance(h)
    print(f"Wallet after: {after}")
    if before is not None and after is not None and d.get("duration"):
        spent = round(before - after, 4)
        print(f"Spent: ${spent} for {d['duration']} s = ${spent / float(d['duration']) * 60:.2f} per minute of face")
    if d.get("status") != "completed":
        sys.exit(1)


LINES = {"en": "Welcome to AI This Week. I'm Wissam Kishek. I've spent twenty-five years in enterprise software, "
               "across the Middle East, Turkey and Africa.",
         "ar": "أهلا فيكم بأسبوع الذكاء الاصطناعي، معكم وسام كيشك. صرلي خمسة وعشرين سنة بالبرمجيات المؤسسية، "
               "بالشرق الأوسط وتركيا وأفريقيا."}
MOTION = ("He speaks to the camera like a calm news presenter: small natural hand gestures at chest height on the "
          "key words, a slight nod, relaxed shoulders, steady eye contact.")
FLOOR_USD = 8.0   # face-compare starts nothing under this


def variants(image_url: str, audio: dict[str, str]) -> list[dict]:
    """The side-by-side jobs (founder 2026-11-23: is the newer engine, or a lip-sync pass, better than what the
    show uses?). One line per language, the same picture and sound in every job of a language."""
    def video(lang: str, **extra) -> dict:
        return {"type": "image", "image": {"type": "url", "url": image_url}, "audio_url": audio[lang],
                "resolution": "1080p", "aspect_ratio": "auto", "title": "engine comparison", **extra}
    six = {"engine": {"type": "heygen-avatar-6"}}
    out = []
    for lang in audio:
        out += [{"name": f"{lang} avatar-iv (today)", "lang": lang, "kind": "video", "body": video(lang)},
                {"name": f"{lang} avatar-6", "lang": lang, "kind": "video", "body": video(lang, **six)}]
        if lang == "en":
            out.append({"name": "en avatar-6 + gestures", "lang": lang, "kind": "video",
                        "body": video(lang, **six, motion_prompt=MOTION)})
        out.append({"name": f"{lang} avatar-iv + precision lip-sync", "lang": lang, "kind": "lipsync",
                    "of": f"{lang} avatar-iv (today)"})
    return out


def _wait(h: dict, path: str, sleep, wait_s: int = 1500, every_s: int = 20) -> dict:
    d: dict = {}
    for _ in range(max(1, wait_s // every_s)):
        sleep(every_s)
        g = requests.get(f"{BASE}{path}", headers=h, timeout=60)
        d = (g.json() or {}).get("data", {}) if g.ok else {}
        if d.get("status") in ("completed", "failed"):
            break
    return d


def face_compare(image_url: str) -> None:
    """Spends money (about seven 10-second clips): only on the founder's word. Nothing is retried; a refused
    variant is reported and the rest go on. The wallet is read around every job, so each price is measured."""
    import time
    import uuid
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import yaml
    from pipeline.video import tts
    key = os.environ.get("HEYGEN_API_KEY", "")
    if not key:
        sys.exit("HEYGEN_API_KEY is not set")
    h = {"X-Api-Key": key, "Accept": "application/json"}
    start = balance(h)
    print(f"Wallet at the start: {start}")
    if start is None or float(start) < FLOOR_USD:
        sys.exit(f"The wallet could not be read or holds under ${FLOOR_USD:g}: nothing was started")
    hg = yaml.safe_load((Path(__file__).resolve().parents[1] / "config" / "settings.yaml").read_text(encoding="utf-8"))["video"]["heygen"]
    audio = {}
    for lang, voice in (("en", hg["voice_id_en"]), ("ar", hg["voice_id"])):
        audio[lang], secs = tts.speak(LINES[lang], voice, lang, key)
        print(f"Speech {lang}: {secs:.1f} s  {audio[lang]}")
    done: dict[str, str] = {}
    rows = []
    for v in variants(image_url, audio):
        before = balance(h)
        post = {**h, "Content-Type": "application/json", "Idempotency-Key": f"compare-{uuid.uuid4().hex}"}
        if v["kind"] == "video":
            r = requests.post(f"{BASE}/v3/videos", timeout=120, headers=post, json=v["body"])
            ident, path = (r.json().get("data") or {}).get("video_id") if r.ok else None, "/v3/videos/"
        else:
            if v["of"] not in done:
                rows.append((v["name"], "skipped: its source clip was not made", "", ""))
                continue
            r = requests.post(f"{BASE}/v3/lipsyncs", timeout=120, headers=post,
                              json={"video": {"type": "url", "url": done[v["of"]]},
                                    "audio": {"type": "url", "url": audio[v["lang"]]}, "mode": "precision",
                                    "title": "engine comparison"})
            ident, path = (r.json().get("data") or {}).get("lipsync_id") if r.ok else None, "/v3/lipsyncs/"
        if not ident:
            rows.append((v["name"], f"refused: HTTP {r.status_code} {r.text[:200]}", "", ""))
            continue
        d = _wait(h, path + ident, time.sleep)
        time.sleep(30)   # the charge may post a little after the render
        after = balance(h)
        spent = "" if before is None or after is None else f"${float(before) - float(after):.3f}"
        if d.get("status") == "completed" and d.get("video_url"):
            done[v["name"]] = d["video_url"]
            rows.append((v["name"], f"done, {d.get('duration')} s", spent, d["video_url"]))
        else:
            rows.append((v["name"], f"{d.get('status') or 'not ready'}: {d.get('failure_code')} {d.get('failure_message')}", spent, ""))
    end = balance(h)
    print("\n## Comparison")
    for name, state, spent, url in rows:
        print(f"- {name} | {state} | {spent} | {url}")
    if end is not None:
        print(f"\nWallet at the end: {end}  (the whole test: ${float(start) - float(end):.2f})")


if __name__ == "__main__":
    if sys.argv[1:2] == ["face-test"]:
        face_test(sys.argv[2], sys.argv[3])
    elif sys.argv[1:2] == ["face-compare"]:
        face_compare(sys.argv[2])
    else:
        main(int(sys.argv[1]) if len(sys.argv) > 1 else 14)
