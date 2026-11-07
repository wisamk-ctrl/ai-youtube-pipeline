"""
The YouTube description, built only from what the week already holds (never made up):

    Arabic hook          the cold open as approved in script.md (or plan.hook_ar if the plan has one)
    chapters             "00:00 …" from the script's [Section] titles at their times in the FINAL
                         video (timeline.json from phase post). YouTube shows chapters only when
                         there are ≥ 3, the first at 00:00 and each ≥ 10 s; when that cannot be met
                         the section titles are listed as plain headlines instead.
    sources              the items the source map cites (else the plan's items), tier A/B outlets
                         when any are present; radar notes and mailto links never
    stock credits        Pixabay / Pexels authors from credits.json
    disclosure           AI digital twin + informational-only line, then the hashtags

English title/description go into the Data API `localizations` field when the plan has English
fields. YouTube rejects '<' and '>' in titles and descriptions, so they are stripped.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

DESC_LIMIT = 5000
TITLE_LIMIT = 100
MIN_CHAPTER_S = 10.0
DISCLOSURE_AR = ("تنويه: يقدّم هذه الحلقة توأم رقمي لوسام مولّد بالذكاء الاصطناعي، بموافقة وسام. "
                 "المحتوى للمعلومات العامة فقط وليس نصيحة استثمارية أو قانونية.")
DISCLOSURE_EN = ("Note: this episode is presented by Wissam's AI digital twin, with his consent. "
                 "Informational only; not investment or legal advice.")


def clean(text: str) -> str:
    return re.sub(r"[<>]", "", text or "").strip()


# ── Chapters ────────────────────────────────────────────────────────────────
def fmt_time(t: float) -> str:
    s = int(t)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"


def chapters(sections: list[tuple[str, float]], duration: float | None = None,
             min_len: float = MIN_CHAPTER_S) -> list[tuple[float, str]]:
    """YouTube-valid chapters, or [] when they cannot be made valid.

    The first chapter is forced to 00:00. A chapter shorter than `min_len` gives way to the one after
    it (the content is still under the previous chapter); a last chapter shorter than `min_len`
    before the end is dropped. Fewer than 3 left → no chapters at all."""
    marks = sorted(((max(0.0, float(t)), clean(title)) for title, t in sections if clean(title)), key=lambda m: m[0])
    if not marks:
        return []
    kept = [(0.0, marks[0][1])]
    for t, title in marks[1:]:
        while len(kept) > 1 and t - kept[-1][0] < min_len:
            kept.pop()
        if t - kept[-1][0] >= min_len:
            kept.append((t, title))
    if duration is not None:
        while len(kept) > 1 and duration - kept[-1][0] < min_len:
            kept.pop()
    return kept if len(kept) >= 3 else []


def chapter_lines(ch: list[tuple[float, str]]) -> list[str]:
    return [f"{fmt_time(t)} {title}" for t, title in ch]


def load_sections(out_dir: Path, cfg: dict[str, Any]) -> tuple[list[tuple[str, float]], float | None]:
    """Section titles and final-video start times: timeline.json, else from script.md + the final
    captions (subtitles.final.srt carries the sting shift), else word-count estimates."""
    tl = out_dir / "timeline.json"
    if tl.exists():
        d = json.loads(tl.read_text(encoding="utf-8"))
        return [(s["title"], float(s["start"])) for s in d.get("sections", [])], d.get("duration")
    script = out_dir / "script.md"
    if not script.exists():
        return [], None
    from pipeline.post.packaging import section_marks
    srt = next((p for p in (out_dir / "subtitles.final.srt", out_dir / "subtitles.srt") if p.exists()), None)
    return section_marks(script.read_text(encoding="utf-8"), srt, int(cfg["scripting"]["words_per_minute"])), None


# ── Hook ────────────────────────────────────────────────────────────────────
def hook_ar(plan: dict[str, Any], script: str | None, max_chars: int = 280) -> str:
    """The cold open's first sentences, exactly as approved (braced names as captions show them)."""
    for key in ("hook_ar", "cold_open_hook_ar"):
        if plan.get(key):
            return clean(str(plan[key]))
    if not script:
        return ""
    from pipeline.script_format import MARKER_RE, caption_text, spoken_text, spoken_words
    marks = [m for m in MARKER_RE.finditer(script) if m.group("body").strip().lower().startswith("section")]
    cold = script[: marks[1].start()] if len(marks) > 1 else script
    words = [caption_text(w).strip() for w in spoken_words(spoken_text(cold))]
    out = ""
    for w in words:
        if len(out) + len(w) + 1 > max_chars:
            break
        out = f"{out} {w}".strip()
        if len(out) > 80 and w.endswith((".", "؟", "?", "!", "…")):
            break
    return clean(out)


def headlines_ar(plan: dict[str, Any], sections: list[tuple[str, float]]) -> list[str]:
    """Arabic story headlines: the plan's own Arabic headlines if it has them, else the script's
    [Section] titles without the cold open and the sign-off."""
    own = [clean(s.get("headline_ar", "")) for s in plan.get("segments", []) if s.get("headline_ar")]
    if own:
        return own
    titles = [clean(t) for t, _ in sections if clean(t)]
    return titles[1:-1] if len(titles) > 2 else titles


# ── Sources and credits ─────────────────────────────────────────────────────
def cited_urls(source_map_md: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"\]\((https?://[^)\s]+)\)", source_map_md)))


def pick_sources(out_dir: Path, plan: dict[str, Any], items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Source items for the description: cited in source_map.md (else used by the plan), never radar
    notes or mailto links; only tier A/B outlets when the tiers say any are present."""
    from pipeline.ingestion.publishers import is_radar, tier_of
    from pipeline.models import NewsItem
    smap = out_dir / "source_map.md"
    urls = cited_urls(smap.read_text(encoding="utf-8")) if smap.exists() else []
    if urls:
        by_url = {i["url"]: i for i in items}
        chosen = [by_url[u] for u in urls if u in by_url]
    else:
        used = {i for s in plan.get("segments", []) for i in s.get("item_ids", [])} | set(plan.get("quick_fire_item_ids", []))
        chosen = [i for i in items if i.get("id") in used]
    out, tiers = [], []
    for d in chosen:
        if not d.get("url") or d["url"].startswith("mailto:"):
            continue
        try:
            item = NewsItem.from_dict(d)
            if is_radar(item):
                continue
            tiers.append(tier_of(item))
        except Exception:  # noqa: BLE001 — an odd row is listed without a tier
            tiers.append("")
        out.append(d)
    if any(t in ("A", "B") for t in tiers):
        out = [d for d, t in zip(out, tiers) if t in ("A", "B")]
    seen, uniq = set(), []
    for d in out:
        if d["url"] not in seen:
            seen.add(d["url"])
            uniq.append(d)
    return uniq


def credits_line(credits: list[dict[str, Any]], lang: str = "ar") -> str:
    by: dict[str, list[str]] = {}
    for c in credits:
        prov = str(c.get("provider") or "stock").capitalize()
        name = clean(str(c.get("author") or ""))
        names = by.setdefault(prov, [])
        if name and name not in names:
            names.append(name)
    if not by:
        return ""
    sep = "، " if lang == "ar" else ", "
    parts = [f"{p} ({sep.join(n)})" if n else p for p, n in by.items()]
    return ("لقطات مرئية من: " if lang == "ar" else "Stock footage: ") + " · ".join(parts)


# ── Assembly ────────────────────────────────────────────────────────────────
def _fit(head: list[str], sources: list[str], tail: list[str], limit: int = DESC_LIMIT) -> str:
    """Sources are trimmed (never the disclosure or the hashtags) to stay inside YouTube's limit."""
    src = list(sources)
    while True:
        text = "\n".join(head + src + tail)
        if len(text) <= limit or len(src) <= 1:
            return text[:limit]
        src.pop()


def build_description(plan: dict[str, Any], sources: list[dict[str, Any]], cfg: dict[str, Any],
                      sections: list[tuple[str, float]] | None = None, duration: float | None = None,
                      script: str | None = None, credits: list[dict[str, Any]] | None = None) -> str:
    sections = sections or []
    head = []
    hook = hook_ar(plan, script)
    if hook:
        head += [hook, ""]
    ch = chapters(sections, duration)
    heads = headlines_ar(plan, sections)
    if ch:
        head += ["في هذه الحلقة:", *chapter_lines(ch), ""]
    elif heads:
        head += ["في هذه الحلقة:", *[f"• {h}" for h in heads], ""]
    src = [f"- {clean(s.get('title', ''))}: {s['url']}" for s in sources]
    src = (["المصادر:"] + src + [""]) if src else []
    tail = []
    cl = credits_line(credits or [])
    if cl:
        tail += [cl, ""]
    tail += [DISCLOSURE_AR, "", " ".join(cfg.get("publish", {}).get("hashtags", []))]
    return clean(_fit(head, src, tail))


def localizations(plan: dict[str, Any], sources: list[dict[str, Any]], cfg: dict[str, Any]) -> dict[str, Any]:
    """{"en": {"title", "description"}} from the plan's English fields; {} when it has none."""
    hook = clean(plan.get("cold_open_hook_en", ""))
    heads = [clean(s.get("headline_en", "")) for s in plan.get("segments", []) if s.get("headline_en")]
    title = clean(plan.get("episode_title_en", ""))
    if not (title or hook or heads):
        return {}
    if not title:
        show = cfg.get("publish", {}).get("show_name_en", "AI Week")
        title = f"{show} (Arabic): {heads[0]}" if heads else f"{show} (Arabic)"
    lines = [hook, ""] if hook else []
    if heads:
        lines += ["In this episode:", *[f"• {h}" for h in heads], ""]
    if sources:
        lines += ["Sources:", *[f"- {clean(s.get('title', ''))}: {s['url']}" for s in sources], ""]
    lines += [DISCLOSURE_EN]
    return {"en": {"title": title[:TITLE_LIMIT], "description": clean("\n".join(lines))[:DESC_LIMIT]}}
