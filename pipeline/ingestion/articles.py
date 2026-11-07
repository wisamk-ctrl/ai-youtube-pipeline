"""
Full articles behind Google News headlines, and syndicated copies counted once.

A Google News RSS item carries only a headline and the publisher's name, so a script line
«حسب رويترز …» used to be checked against a headline. This module, best effort and never
fatal:

  * resolves the news.google.com link to the publisher's own URL,
  * fetches the page and keeps the article text (a small readability pass: the <p> blocks
    of the main content, scripts/navigation/footers removed),
  * with a per-request timeout and a cap on fetches per run; any failure keeps the headline.

Syndicated copies (one wire story republished by several outlets, or the same headline
under two watched names) are detected by near-identical headline or opening text, and the
copy from the best-tier publisher is kept, so one story counts once.
"""

from __future__ import annotations

import base64
import json
import logging
import re
from difflib import SequenceMatcher
from typing import Any
from urllib.parse import quote, urlparse

import requests

from pipeline.ingestion.publishers import load_publishers
from pipeline.ingestion.text_utils import BROWSER_HEADERS, strip_html, truncate
from pipeline.models import NewsItem

log = logging.getLogger(__name__)

_URL_IN_BYTES = re.compile(rb"https?://[\x21-\x7e]+")
_DROP_BLOCKS = re.compile(r"<(script|style|noscript|nav|header|footer|aside|form|figure|svg)\b.*?</\1>", re.S | re.I)
_PARA = re.compile(r"<p\b[^>]*>(.*?)</p>", re.S | re.I)
_ARTICLE = re.compile(r"<article\b[^>]*>(.*?)</article>", re.S | re.I)
_TIER_RANK = {"A": 0, "B": 1, "C": 2, "R": 3}


def _is_google(url: str) -> bool:
    return (urlparse(url).hostname or "").endswith("news.google.com")


def _decode_legacy(article_id: str) -> str:
    """Older Google News ids are base64 of a protobuf that contains the URL in clear."""
    try:
        raw = base64.urlsafe_b64decode(article_id + "=" * (-len(article_id) % 4))
    except Exception:  # noqa: BLE001
        return ""
    m = _URL_IN_BYTES.search(raw)
    return m.group(0).decode("ascii", "ignore") if m else ""


def _decode_batchexecute(article_id: str, timeout: float) -> str:
    """Current ids need Google's own decoder endpoint, with a signature read from the article page."""
    page = requests.get(f"https://news.google.com/rss/articles/{article_id}", headers=BROWSER_HEADERS, timeout=timeout)
    page.raise_for_status()
    sg = re.search(r'data-n-a-sg="([^"]+)"', page.text)
    ts = re.search(r'data-n-a-ts="([^"]+)"', page.text)
    if not (sg and ts):
        return ""
    inner = ('["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],'
             f'"X","X",1,[1,1,1],1,1,null,0,0,null,0],"{article_id}",{ts.group(1)},"{sg.group(1)}"]')
    body = "f.req=" + quote(json.dumps([[["Fbv4je", inner]]]))
    r = requests.post("https://news.google.com/_/DotsSplashUi/data/batchexecute", data=body, timeout=timeout,
                      headers={**BROWSER_HEADERS, "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"})
    r.raise_for_status()
    parsed = json.loads(r.text.split("\n\n", 1)[1])[:-2]
    return str(json.loads(parsed[0][2])[1])


def resolve_google_news(url: str, timeout: float) -> str:
    """The publisher's URL behind a news.google.com link, or "" when it cannot be resolved."""
    if not _is_google(url):
        return url
    m = re.search(r"/articles/([^/?#]+)", url)
    if not m:
        return ""
    found = _decode_legacy(m.group(1))
    if found and not _is_google(found):
        return found
    try:
        found = _decode_batchexecute(m.group(1), timeout)
    except Exception as exc:  # noqa: BLE001 — best effort
        log.debug("Google News decode failed for %s: %s", url, exc)
        return ""
    return found if isinstance(found, str) and found.startswith("http") and not _is_google(found) else ""


def extract_text(page_html: str) -> str:
    """A minimal readability pass: paragraphs of the <article> (or the page), boilerplate dropped."""
    if not isinstance(page_html, str):
        return ""
    doc = _DROP_BLOCKS.sub(" ", page_html)
    scope = max(_ARTICLE.findall(doc), key=len, default=doc)
    paras = [strip_html(p) for p in _PARA.findall(scope)]
    paras = [p for p in paras if len(p) >= 40 and not p.lower().startswith(("cookie", "sign up", "subscribe"))]
    return " ".join(paras)


def fetch_article(url: str, timeout: float, max_chars: int) -> str:
    r = requests.get(url, headers=BROWSER_HEADERS, timeout=timeout)
    r.raise_for_status()
    return truncate(extract_text(r.text), max_chars)


def enrich(items: list[NewsItem], opts: dict[str, Any]) -> int:
    """Replace headline-only Google News items with the publisher URL and article text, in place.

    Returns how many items gained text. Never raises: a failed item keeps its headline."""
    if not opts.get("enabled", False):
        return 0
    timeout, cap = float(opts.get("timeout_s", 8)), int(opts.get("max_items", 40))
    max_chars = int(opts.get("max_chars", 2500))
    gained = 0
    for item in items[:cap]:
        try:
            target = resolve_google_news(item.url, timeout)
            if not target:
                continue
            item.url = target
            text = fetch_article(target, timeout, max_chars)
            if len(text) > len(item.summary) + 80:
                item.summary = text
                gained += 1
        except Exception as exc:  # noqa: BLE001 — paywall, 403, timeout: the headline stays
            log.debug("Article fetch failed for %s: %s", item.url, exc)
    log.info("Articles: %d of %d Google News items now carry article text", gained, min(len(items), cap))
    return gained


# ── Syndication ──────────────────────────────────────────────────────────────
def is_syndicated(a: NewsItem, b: NewsItem, threshold: float = 0.82) -> bool:
    """Same story republished: near-identical headline, or the same opening paragraph."""
    if SequenceMatcher(None, a.normalized_title, b.normalized_title).ratio() >= threshold:
        return True
    pa, pb = a.summary[:300].lower(), b.summary[:300].lower()
    return len(pa) >= 200 and len(pb) >= 200 and SequenceMatcher(None, pa, pb).ratio() >= 0.9


def syndication_groups(items: list[NewsItem], threshold: float = 0.82) -> dict[str, str]:
    """item id → id of the first copy of its story, so callers can count a story once."""
    reps: list[NewsItem] = []
    out: dict[str, str] = {}
    for i in items:
        rep = next((r for r in reps if is_syndicated(i, r, threshold)), None)
        if rep is None:
            reps.append(i)
            rep = i
        out[i.id] = rep.id
    return out


def collapse_syndicated(items: list[NewsItem], threshold: float = 0.82) -> list[NewsItem]:
    """Keep one copy per story: the best-tier publisher's, then the longest text. Watched names merge."""
    pubs = load_publishers()
    ranked = sorted(items, key=lambda i: (_TIER_RANK.get(pubs.tier(i), 2), -len(i.summary)))
    kept: list[NewsItem] = []
    for i in ranked:
        dup = next((k for k in kept if is_syndicated(i, k, threshold)), None)
        if dup is None:
            kept.append(i)
        else:
            dup.entities = sorted(set(dup.entities) | set(i.entities))
    if len(kept) < len(items):
        log.info("Syndication: %d copies of %d stories collapsed", len(items) - len(kept), len(kept))
    order = {id(i): n for n, i in enumerate(items)}
    return sorted(kept, key=lambda i: order[id(i)])
