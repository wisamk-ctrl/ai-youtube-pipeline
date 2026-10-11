"""
Phase 1d — newsletters that only arrive by email (AlphaSignal, TLDR AI, ...).

Reads the last week's newsletter emails through the Gmail API and splits each
one into its individual stories, so a single TLDR email yields 8-12 NewsItems
rather than one 3,000-word blob that the scorer can't rank.

Splitting heuristic (works for TLDR, AlphaSignal, The Rundown and most
Beehiiv/Substack newsletters): a story starts at a short line that is
followed by a paragraph, and TLDR-style headlines carry "(N minute read)".
Unsplittable emails fall back to one item per email — never lost, just coarse.
"""

from __future__ import annotations

import base64
import logging
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any

from pipeline.ingestion.text_utils import strip_html, truncate
from pipeline.models import NewsItem

log = logging.getLogger(__name__)

# The headline line may carry the (tracking) link that _html_to_text_keeping_links appends.
HEADLINE_RE = re.compile(r"^(?P<title>.{12,140}?)\s*\((?P<mins>\d+) minute read\)\s*(?:https?://\S+)?\s*$",
                         re.IGNORECASE | re.MULTILINE)
URL_RE = re.compile(r"https?://[^\s\)\]\"'<>]+")
TRACKING_HOSTS = ("tracking.", "click.", "links.", "email.", "mailchi.mp", "list-manage", "beehiiv.com/c/")


def _body_html(payload: dict[str, Any]) -> str:
    """Walk the MIME tree and return the first text/html part (else text/plain)."""
    stack, plain = [payload], ""
    while stack:
        part = stack.pop()
        mime = part.get("mimeType", "")
        data = part.get("body", {}).get("data")
        if data:
            text = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
            if mime == "text/html":
                return text
            if mime == "text/plain" and not plain:
                plain = text
        stack.extend(part.get("parts", []))
    return plain


def _html_to_text_keeping_links(html: str) -> str:
    """Like strip_html, but turns <a href="X">label</a> into "label X" so the
    story's source link survives, and keeps paragraph breaks as newlines."""
    html = re.sub(r"<a\s[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", r"\2 \1 ", html, flags=re.I | re.S)
    html = re.sub(r"</(p|div|h\d|li|tr|br)\s*>|<br\s*/?>", "\n", html, flags=re.I)
    return "\n".join(strip_html(line) for line in html.split("\n"))


def _first_real_url(text: str, sender_domain: str) -> str:
    for url in URL_RE.findall(text):
        if sender_domain in url or any(t in url for t in TRACKING_HOSTS):
            continue  # unsubscribe / tracking / self links
        if any(s in url for s in ("unsubscribe", "manage", "preferences", "twitter.com/intent")):
            continue
        return url
    return ""


def split_stories(text: str, sender_domain: str) -> list[tuple[str, str, str]]:
    """Return (title, body, url) per story. Empty list if no headline pattern matched."""
    matches = list(HEADLINE_RE.finditer(text))
    stories = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end():end].strip()
        # Stop at section banners like "QUICK LINKS" / sponsor blocks.
        body = re.split(r"\n[A-Z][A-Z &]{6,}\n", body)[0].strip()
        if len(body) < 40:
            continue
        stories.append((m.group("title").strip(), body, _first_real_url(body, sender_domain)))
    return stories


def email_to_items(msg: dict[str, Any], source_name: str, weight: float) -> list[NewsItem]:
    headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
    sender = headers.get("from", "")
    sender_domain = sender.split("@")[-1].strip("> ") if "@" in sender else ""
    try:
        published = parsedate_to_datetime(headers["date"]).astimezone(timezone.utc)
    except (KeyError, ValueError, TypeError):
        published = datetime.fromtimestamp(int(msg.get("internalDate", 0)) / 1000, tz=timezone.utc)

    text = _html_to_text_keeping_links(_body_html(msg["payload"]))
    subject = headers.get("subject", source_name)
    stories = split_stories(text, sender_domain)
    if not stories:
        log.info("Gmail %s: no story pattern in %r — keeping whole email", source_name, subject)
        stories = [(subject, text, _first_real_url(text, sender_domain))]

    items = []
    for n, (title, body, url) in enumerate(stories):
        items.append(NewsItem(
            source=source_name, source_type="rss", title=title,
            summary=truncate(URL_RE.sub("", body).strip(), 2500),
            # No link → synthesize a stable one so dedupe/ID logic still works.
            url=url or f"mailto:{sender_domain}#{msg['id']}-{n}",
            published=published, author=sender, source_weight=weight,
        ))
    return items


def fetch_gmail_newsletters(cfg: dict[str, Any]) -> list[NewsItem]:
    gcfg = cfg["ingestion"].get("gmail", {})
    if not gcfg.get("enabled"):
        return []
    from pipeline.google_auth import client  # lazy: google libs only needed when enabled

    gmail = client("gmail")
    since = datetime.now(timezone.utc) - timedelta(days=cfg["ingestion"]["lookback_days"])
    out: list[NewsItem] = []
    for nl in gcfg["newsletters"]:
        query = f"{nl['query']} after:{since:%Y/%m/%d}"
        try:
            ids = gmail.users().messages().list(userId="me", q=query, maxResults=20).execute().get("messages", [])
            for ref in ids:
                msg = gmail.users().messages().get(userId="me", id=ref["id"], format="full").execute()
                out.extend(email_to_items(msg, nl["name"], nl.get("weight", 1.0)))
            log.info("Gmail %-20s %2d emails in window", nl["name"], len(ids))
        except Exception as exc:  # noqa: BLE001 — one newsletter must not kill the run
            log.error("Gmail newsletter %r failed: %s", nl["name"], exc)
    return out
