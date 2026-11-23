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


if __name__ == "__main__":
    if sys.argv[1:2] == ["face-test"]:
        face_test(sys.argv[2], sys.argv[3])
    else:
        main(int(sys.argv[1]) if len(sys.argv) > 1 else 14)
