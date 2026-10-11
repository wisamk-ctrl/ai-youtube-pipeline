"""
Phase 1b — X (Twitter) API v2 ingestion.

Uses the official API (not HTML scraping, which breaks weekly and violates the
X Terms of Service). Flow:

  1. Resolve the curated @handles to numeric user IDs   (GET /2/users/by)
  2. Pull each account's original posts for the week   (GET /2/users/:id/tweets)
  3. Rank all posts by a weighted engagement score and keep the top N (default 10)

Cost / access note: reading timelines requires a paid X API tier (Basic or
higher). Each weekly run reads at most  len(accounts) × max_posts_per_account
posts, so budget the monthly read cap accordingly.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from pipeline.config import require_env
from pipeline.models import NewsItem

log = logging.getLogger(__name__)

API = "https://api.x.com/2"


class XClient:
    def __init__(self, bearer_token: str, timeout: int = 20) -> None:
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {bearer_token}"
        self.timeout = timeout

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        """GET with rate-limit awareness.

        On 429, X returns `x-rate-limit-reset` (epoch seconds). We sleep until
        then (capped at 15 min) and retry once, rather than failing the run.
        """
        for attempt in range(2):
            resp = self.session.get(f"{API}{path}", params=params, timeout=self.timeout)
            if resp.status_code == 429 and attempt == 0:
                reset = int(resp.headers.get("x-rate-limit-reset", time.time() + 60))
                wait = min(max(reset - time.time(), 1), 900)
                log.warning("X rate limit hit; sleeping %.0fs", wait)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
        raise RuntimeError("X API still rate-limited after waiting")

    def resolve_users(self, handles: list[str]) -> dict[str, str]:
        """Map user_id → handle. The endpoint accepts up to 100 usernames per call."""
        out: dict[str, str] = {}
        for i in range(0, len(handles), 100):
            batch = [h.lstrip("@") for h in handles[i : i + 100]]
            data = self._get("/users/by", {"usernames": ",".join(batch)})
            for user in data.get("data", []):
                out[user["id"]] = user["username"]
            for err in data.get("errors", []):  # suspended/renamed accounts
                log.warning("X user lookup issue: %s", err.get("detail"))
        return out

    def user_posts(self, user_id: str, since: datetime, max_posts: int) -> list[dict[str, Any]]:
        """Original posts (no replies, no reposts) since `since`, paginated."""
        params: dict[str, Any] = {
            "start_time": since.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "max_results": 100,
            "exclude": "replies,retweets",  # replies/reposts are noise for a roundup
            "tweet.fields": "created_at,public_metrics,entities,note_tweet",
        }
        posts: list[dict[str, Any]] = []
        while len(posts) < max_posts:
            data = self._get(f"/users/{user_id}/tweets", params)
            posts.extend(data.get("data", []))
            token = data.get("meta", {}).get("next_token")
            if not token:
                break
            params["pagination_token"] = token
        return posts[:max_posts]


def engagement_score(metrics: dict[str, int]) -> int:
    """Weighted engagement. Reposts/quotes signal 'worth sharing' more than likes."""
    return (
        metrics.get("like_count", 0)
        + 2 * metrics.get("retweet_count", 0)
        + 3 * metrics.get("quote_count", 0)
        + metrics.get("reply_count", 0) // 2
    )


def _post_text(post: dict[str, Any]) -> str:
    """Long posts (>280 chars) carry their full text in note_tweet."""
    return (post.get("note_tweet") or {}).get("text") or post.get("text", "")


def _post_link(post: dict[str, Any], handle: str) -> str:
    """Prefer the first external link (the actual news source) over the post URL."""
    for u in (post.get("entities") or {}).get("urls", []):
        expanded = u.get("expanded_url", "")
        if expanded and "x.com" not in expanded and "twitter.com" not in expanded:
            return expanded
    return f"https://x.com/{handle}/status/{post['id']}"


def fetch_top_posts(cfg: dict[str, Any]) -> list[NewsItem]:
    """Return the week's top-N posts across the curated accounts."""
    xcfg = cfg["ingestion"]["x"]
    if not xcfg.get("enabled", True):
        return []

    client = XClient(require_env("X_BEARER_TOKEN"), cfg["ingestion"]["request_timeout_s"])
    since = datetime.now(timezone.utc) - timedelta(days=cfg["ingestion"]["lookback_days"])

    users = client.resolve_users(xcfg["accounts"])
    candidates: list[NewsItem] = []
    for user_id, handle in users.items():
        try:
            posts = client.user_posts(user_id, since, xcfg["max_posts_per_account"])
        except requests.HTTPError as exc:
            log.error("X timeline for @%s failed: %s", handle, exc)
            continue
        for post in posts:
            text = _post_text(post)
            candidates.append(
                NewsItem(
                    source=f"@{handle}",
                    source_type="x",
                    title=text.split("\n", 1)[0][:140],
                    summary=text,
                    url=_post_link(post, handle),
                    published=datetime.fromisoformat(post["created_at"].replace("Z", "+00:00")),
                    author=handle,
                    engagement=engagement_score(post.get("public_metrics", {})),
                )
            )
        log.info("X  @%-26s %3d posts in window", handle, len(posts))

    # Engagement is only comparable *within* X, so the top-N cut happens here,
    # before X items are mixed with RSS items in the relevance scorer.
    candidates.sort(key=lambda i: i.engagement, reverse=True)
    return candidates[: xcfg["top_n"]]
