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


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 14)
