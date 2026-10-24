"""Markdown report of what was ingested this week, grouped by source, with the kept items
marked — so the review issue shows what the writer could draw on, not only what it used.
Kept compact on purpose: Google News fans out to hundreds of outlets and a GitHub issue body
is capped at 65k characters."""

from __future__ import annotations

from collections import defaultdict

from pipeline.models import NewsItem


def _line(i: NewsItem, kept: bool) -> str:
    tag = f", {i.track}" if i.track else ""
    return f"- {'✅' if kept else '·'} [{i.title.strip()[:100]}]({i.url}) — score {i.score:.1f}{tag}"


def sources_md(all_items: list[NewsItem], kept: list[NewsItem], youtube_per_channel: int = 8) -> str:
    kept_urls = {i.url for i in kept}
    by_source: dict[str, list[NewsItem]] = defaultdict(list)
    for i in all_items:
        by_source[(i.source_type, i.source)].append(i)
    rows = sorted(by_source.items(), key=lambda kv: (-sum(i.url in kept_urls for i in kv[1]), -len(kv[1])))
    main = [(k, v) for k, v in rows if len(v) >= 3 or any(i.url in kept_urls for i in v) or k[0] == "youtube"]
    tail = [(k, v) for k, v in rows if (k, v) not in main]

    out = [f"## Sources this week · {len(all_items)} items from {len(by_source)} sources, {len(kept)} kept for the writer\n"]
    out.append("| source | items | kept |\n|---|---|---|")
    out += [f"| {t}: {s} | {len(v)} | {sum(i.url in kept_urls for i in v)} |" for (t, s), v in main]
    if tail:
        out.append(f"| … {len(tail)} more outlets with 1–2 items each (Google News long tail) | {sum(len(v) for _, v in tail)} | 0 |")

    yt = [(k, v) for k, v in rows if k[0] == "youtube"]
    if yt:
        out.append(f"\n### YouTube channels ({sum(len(v) for _, v in yt)} videos in window)\n")
        for (_, name), v in yt:
            out.append(f"**{name}**")
            out += [_line(i, i.url in kept_urls) for i in sorted(v, key=lambda x: -x.score)[:youtube_per_channel]]
    out.append(f"\n<details><summary>Items kept for the writer ({len(kept)})</summary>\n")
    for (t, s), v in rows:
        ks = [i for i in v if i.url in kept_urls]
        if ks and t != "youtube":
            out.append(f"\n**{t}: {s}**")
            out += [_line(i, True) for i in sorted(ks, key=lambda x: -x.score)]
    out.append("\n</details>")
    return "\n".join(out)
