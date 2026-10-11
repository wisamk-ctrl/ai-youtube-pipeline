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
