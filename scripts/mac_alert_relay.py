#!/usr/bin/python3
"""Pipeline alerts to the founder's WhatsApp, through the bridge already on his Mac (founder 2026-11-21: "can we use
the same? It's already configured").

GitHub's runners cannot reach the WhatsApp bridge on localhost:8080, so the Mac fetches instead. Every 10 minutes
(launchd com.wissam.pipeline-alerts) this reads the repo's new issues and comments with the founder's own `gh`
login and sends, once each, to his WhatsApp self-chat:
  urgent  Security: channel changed · Show at risk · Run failed  → WhatsApp + a phone alarm (calendar) + a Mac banner
  info    Episode ready to check · Breaking Short ready          → WhatsApp
Only issues and comments written by the repo owner or the pipeline's bot are read: the repo is public, and a
stranger's comment must never reach the founder's phone.

Sending and the phone alarm are the founder's existing `~/bin/whatsapp_monitor.py` functions (one implementation, so
the two never drift). Runs on macOS's /usr/bin/python3 (3.9), standard library only.
Installed to ~/bin by scripts/install_mac_alert_relay.sh.   `--test` sends one test message.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = "wisamk-ctrl/ai-youtube-pipeline"
GH = "/opt/homebrew/bin/gh"
STATE = Path.home() / "bin" / "state" / "pipeline_alerts.json"
BOT = "github-actions[bot]"
URGENT_TITLES = ("Security:", "Show at risk", "Run failed:")


def _trusted(login: str, owner: str) -> bool:
    return login in (owner, BOT)


def classify_issue(issue: dict, owner: str):
    """(level, text) for a newly opened issue, or None."""
    if "pull_request" in issue or not _trusted((issue.get("user") or {}).get("login", ""), owner):
        return None
    title = issue.get("title", "")
    if title.startswith(URGENT_TITLES):
        return "urgent", f"🔴 AI This Week: {title}\n{issue.get('html_url', '')}"
    return None


def classify_comment(c: dict, titles: dict, owner: str):
    """(level, text) for a new comment, or None. `titles` maps issue number → title (open issues)."""
    if not _trusted((c.get("user") or {}).get("login", ""), owner):
        return None
    body = c.get("body") or ""
    n = int(re.sub(r"\D", "", (c.get("issue_url") or "").rsplit("/", 1)[-1]) or 0)
    url = c.get("html_url", "")
    m = re.search(r"Episode ready to check: `([^`]+)`", body)
    if m:
        return "info", f"🎬 Episode ready to check: {m.group(1)}\nWatch the preview, then reply publish on issue #{n}.\n{url}"
    m = re.match(r"\*\*Ready to check: `([^`]+)`", body)
    if m:
        return "info", f"⚡ Breaking Short ready: {m.group(1)}\nPost it or let it expire.\n{url}"
    title = titles.get(n, "")
    if title.startswith(URGENT_TITLES) and c.get("user", {}).get("login") == BOT:
        return "urgent", f"🔴 AI This Week — update on «{title}»\n{url}"
    return None


def _load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _save(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    state["sent"] = state.get("sent", [])[-500:]
    path.write_text(json.dumps(state, indent=1), encoding="utf-8")


def run(gh, send, alarm, state_path: Path, owner: str, now: str | None = None, since_override: str | None = None) -> int:
    """One pass. gh(path) → parsed JSON; send(text) → True when delivered; alarm(text) for urgent ones.
    Returns the number of alerts sent. The first run only records the time: nothing old is sent."""
    now = now or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    state = _load(state_path)
    if state is None:
        _save(state_path, {"since": now, "sent": []})
        return 0
    since = since_override or (datetime.strptime(state["since"], "%Y-%m-%dT%H:%M:%SZ")
                               - timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    sent = set(state.get("sent", []))
    issues = gh(f"repos/{REPO}/issues?state=open&since={since}&per_page=50") or []
    titles = {i["number"]: i.get("title", "") for i in issues if "number" in i}
    alerts = []
    for i in issues:
        if i.get("created_at", "") >= since:
            alerts.append((f"i{i['id']}", classify_issue(i, owner)))
    for c in gh(f"repos/{REPO}/issues/comments?since={since}&per_page=100") or []:
        alerts.append((f"c{c['id']}", classify_comment(c, titles, owner)))
    count = 0
    for key, found in alerts:
        if not found or key in sent:
            continue
        level, text = found
        if send(text):
            sent.add(key)
            state.setdefault("sent", []).append(key)
            count += 1
            if level == "urgent":
                alarm(text)
    state["since"] = now
    _save(state_path, state)
    return count


def _gh(path: str):
    out = subprocess.run([GH, "api", path], capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError(f"gh api {path.split('?')[0]}: {out.stderr.strip()[:200]}")
    return json.loads(out.stdout or "null")


def main() -> int:
    sys.path.insert(0, str(Path.home() / "bin"))
    import whatsapp_monitor as wm                    # the founder's bridge sender and phone alarm

    def alarm(text: str) -> None:
        wm.send_notification("AI This Week", text.splitlines()[0])
        wm.phone_alert(text.splitlines()[0])

    if "--test" in sys.argv:
        ok = wm.send_whatsapp_to_self("✅ AI This Week alerts are connected. You'll get security, failed-run, "
                                      "episode-ready and breaking-Short messages here.")
        print("test message sent" if ok else "test message FAILED (is the bridge running?)")
        return 0 if ok else 1
    n = run(_gh, wm.send_whatsapp_to_self, alarm, STATE, REPO.split("/")[0])
    print(f"{datetime.now():%Y-%m-%d %H:%M} pipeline alerts: {n} sent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
