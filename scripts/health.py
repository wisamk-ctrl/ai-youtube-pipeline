"""Daily health check and failure alerts (pipeline/publish/health.py; .github/workflows/health.yml).

    python scripts/health.py check                      # connections, posting queue, news watch, scheduled jobs
    python scripts/health.py failed <workflow> <url>    # a workflow run just failed

One open "Health: needs a look" issue. `check` comments when the list of problems changes and closes the issue when
everything is clear again; data/health.json keeps who each connection reaches and the last list. A check that cannot
run is itself reported as a problem.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
STATE = ROOT / "data" / "health.json"
TITLE = "Health: needs a look"


def _issue(gh, repo: str) -> str:
    return gh("issue", "list", "--repo", repo, "--state", "open", "--search", f"{TITLE} in:title",
              "--json", "number", "-q", ".[0].number").strip()


def raise_issue(gh, repo: str, body: str) -> None:
    n = _issue(gh, repo)
    if n:
        gh("issue", "comment", n, "--repo", repo, "--body", body)
    else:
        gh("issue", "create", "--repo", repo, "--title", TITLE, "--body", body)


def gather(gh, repo: str, cfg: dict, state: dict, now: datetime) -> tuple[dict[str, list[str]], dict]:
    from pipeline.publish import health
    from scripts import connect
    problems: dict[str, list[str]] = {}
    ids = state.get("identities", {})
    try:
        text = connect.check()
        problems["Connections"] = health.connection_problems(text, ids)
        ids = {**ids, **health.identities(text)}          # a connection that went missing keeps its old name on record
    except Exception as exc:  # noqa: BLE001 — a check that cannot run is a problem, not a clean result
        problems["Connections"] = [f"The connection check could not run ({type(exc).__name__}: {exc})"]
    for area, path, fn in (("Posting queue", "social_queue.json", health.queue_problems),
                           ("News watch", "news_watch.json", lambda d, n: health.ingest_problems(d.get("runs", []), n))):
        try:
            problems[area] = fn(json.loads((ROOT / "data" / path).read_text(encoding="utf-8")), now)
        except Exception as exc:  # noqa: BLE001
            problems[area] = [f"data/{path} could not be read ({type(exc).__name__}: {exc})"]
    limits = cfg.get("health", {}).get("max_age_hours", {})
    files, last = health.scheduled_workflows(ROOT / ".github" / "workflows"), {}
    try:
        for name in limits:
            last[name] = gh("run", "list", "--repo", repo, "--workflow", files[name], "--status", "success", "--limit", "1",
                            "--json", "createdAt", "-q", ".[0].createdAt").strip() or None
        problems["Scheduled jobs"] = health.workflow_problems(last, now, limits)
    except Exception as exc:  # noqa: BLE001
        problems["Scheduled jobs"] = [f"GitHub's run history could not be read ({type(exc).__name__}: {exc})"]
    floor = cfg.get("health", {}).get("heygen_min_usd")
    if floor is not None and os.environ.get("HEYGEN_API_KEY"):
        try:
            from pipeline.video import faces
            problems["HeyGen wallet"] = health.wallet_problems(faces.balance(os.environ["HEYGEN_API_KEY"]), float(floor))
        except Exception as exc:  # noqa: BLE001
            problems["HeyGen wallet"] = [f"HeyGen's API wallet could not be read ({type(exc).__name__}: {exc})"]
    return problems, ids


def check() -> int:
    from pipeline.config import load_settings
    from pipeline.publish import health
    from scripts.channel import gh
    from scripts.notify import whatsapp
    repo, now = os.environ["GITHUB_REPOSITORY"], datetime.now(timezone.utc)
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    problems, ids = gather(gh, repo, load_settings(), state, now)
    flat = sorted(f"{a}: {p}" for a, items in problems.items() for p in items)
    body = health.report(problems)
    print(body)
    if flat and flat != state.get("problems", []):
        raise_issue(gh, repo, body)
        whatsapp("AI This Week health check: " + "; ".join(flat)[:700])
    elif not flat and (n := _issue(gh, repo)):
        gh("issue", "close", n, "--repo", repo, "--comment", body)
    STATE.write_text(json.dumps({"checked": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "identities": ids, "problems": flat},
                                ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


def failed(workflow: str, url: str) -> int:
    from scripts.channel import gh
    from scripts.notify import whatsapp
    raise_issue(gh, os.environ["GITHUB_REPOSITORY"], f"### A run failed\n- **{workflow}**: {url}\n")
    whatsapp(f"AI This Week: the {workflow} job failed. {url}")
    return 0


if __name__ == "__main__":
    sys.exit(check() if sys.argv[1:2] == ["check"] else failed(*sys.argv[2:4]) if sys.argv[1:2] == ["failed"]
             else print(__doc__) or 2)
