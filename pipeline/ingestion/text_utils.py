"""Small text helpers shared by the ingestion sources (no heavy HTML parser needed)."""

from __future__ import annotations

import html
import re

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def strip_html(raw: str) -> str:
    """Turn newsletter HTML into plain text: drop tags, unescape entities, squash whitespace."""
    text = _TAG_RE.sub(" ", raw or "")
    return _WS_RE.sub(" ", html.unescape(text)).strip()


def truncate(text: str, limit: int) -> str:
    """Cut on a word boundary so the LLM never sees half a word."""
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "…"


# Sent on every feed/page fetch. Datacenter requests with a "bot" User-Agent get 403 from
# Substack and deeplearning.ai and 404 from YouTube's feed endpoint; a plain browser UA passes.
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept": "application/atom+xml, application/rss+xml, application/xml;q=0.9, text/html;q=0.8, */*;q=0.5",
    "Accept-Language": "en-US,en;q=0.8",
}
