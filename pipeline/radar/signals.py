"""
Radar step 1b — hard signals from places where new names show up before the press notices.

  Hugging Face trending   models climbing the trending list (any org)
  OpenRouter              models added to the router this week (= real developer demand)
  GitHub search           AI/agent repos created recently with fast star growth
  Hacker News             front-page stories (Algolia API, points ≥ threshold)

Each returns Signal records keyed by the organisation/model name as the source spells it;
radar.py normalises and merges them with the extraction output. All free, no keys
(GITHUB_TOKEN optional). Product Hunt needs OAuth and arXiv lacks affiliations in its API,
so both are left for a later pass.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

log = logging.getLogger(__name__)
UA = {"User-Agent": "Mozilla/5.0 (compatible; ai-news-roundup/1.0)"}


@dataclass
class Signal:
    name: str                 # org or model name as the source gives it
    kind: str                 # hf_trending | openrouter_new | github_new | hn_front
    strength: float           # 0..1, comparable across kinds
    url: str
    note: str = ""
    track_hint: str = ""      # models | agents | chips | ""
    extra: dict[str, Any] = field(default_factory=dict)


def _get(url: str, timeout: int, **params: Any) -> Any:
    r = requests.get(url, params=params, headers=UA, timeout=timeout)
    r.raise_for_status()
    return r.json()


def hf_trending(timeout: int, limit: int = 50) -> list[Signal]:
    out = []
    try:
        for rank, m in enumerate(_get("https://huggingface.co/api/models", timeout, sort="trendingScore", direction=-1, limit=limit)):
            org = m["id"].split("/")[0]
            out.append(Signal(org, "hf_trending", strength=1 - rank / limit, url=f"https://huggingface.co/{m['id']}",
                              note=f"#{rank + 1} trending, {m.get('downloads', 0):,} downloads", track_hint="models",
                              extra={"model": m["id"], "downloads": m.get("downloads", 0)}))
    except Exception as exc:  # noqa: BLE001
        log.warning("HF trending failed: %s", exc)
    return out


def openrouter_new(timeout: int, days: int) -> list[Signal]:
    out = []
    since = (datetime.now(timezone.utc) - timedelta(days=days)).timestamp()
    try:
        for m in _get("https://openrouter.ai/api/v1/models", timeout)["data"]:
            if m.get("created", 0) >= since:
                org = m["id"].split("/")[0]
                out.append(Signal(org, "openrouter_new", strength=0.8, url=f"https://openrouter.ai/{m['id']}",
                                  note=f"new on OpenRouter: {m.get('name', m['id'])}", track_hint="models",
                                  extra={"model": m["id"], "context": m.get("context_length")}))
    except Exception as exc:  # noqa: BLE001
        log.warning("OpenRouter failed: %s", exc)
    return out


def github_new(timeout: int, days: int, min_stars: int = 300) -> list[Signal]:
    out = []
    headers = dict(UA)
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    since = (datetime.now(timezone.utc) - timedelta(days=days * 4)).date()   # young repos, not just this week's
    q = f"created:>{since} stars:>{min_stars} topic:llm OR topic:ai-agents OR topic:agents OR topic:mcp"
    try:
        r = requests.get("https://api.github.com/search/repositories", params={"q": q, "sort": "stars", "per_page": 30},
                         headers=headers, timeout=timeout)
        r.raise_for_status()
        for repo in r.json().get("items", []):
            out.append(Signal(repo["owner"]["login"], "github_new", strength=min(1.0, repo["stargazers_count"] / 5000),
                              url=repo["html_url"], note=f"{repo['stargazers_count']:,} stars, created {repo['created_at'][:10]}",
                              track_hint="agents", extra={"repo": repo["full_name"], "stars": repo["stargazers_count"]}))
    except Exception as exc:  # noqa: BLE001
        log.warning("GitHub search failed: %s", exc)
    return out


def hn_front(timeout: int, days: int, min_points: int = 150) -> list[Signal]:
    out = []
    since = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
    try:
        for q in ("AI model", "LLM", "AI agent", "inference chip"):
            data = _get("https://hn.algolia.com/api/v1/search", timeout, query=q, tags="story",
                        numericFilters=f"points>{min_points},created_at_i>{since}", hitsPerPage=30)
            for h in data.get("hits", []):
                out.append(Signal(h["title"], "hn_front", strength=min(1.0, h["points"] / 1000),
                                  url=h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}",
                                  note=f"{h['points']} points on Hacker News", extra={"title": h["title"]}))
    except Exception as exc:  # noqa: BLE001
        log.warning("Hacker News failed: %s", exc)
    return out


def collect_signals(cfg: dict[str, Any]) -> list[Signal]:
    r = cfg.get("radar", {})
    t, days = cfg["ingestion"]["request_timeout_s"], cfg["ingestion"]["lookback_days"]
    out: list[Signal] = []
    if r.get("hf_trending", True):
        out += hf_trending(t)
    if r.get("openrouter", True):
        out += openrouter_new(t, days)
    if r.get("github", True):
        out += github_new(t, days, r.get("github_min_stars", 300))
    if r.get("hackernews", True):
        out += hn_front(t, days, r.get("hn_min_points", 150))
    log.info("Radar signals: %d", len(out))
    return out
