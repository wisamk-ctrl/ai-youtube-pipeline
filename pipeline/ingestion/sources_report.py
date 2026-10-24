"""Markdown report of every item ingested this week, grouped by source, with the kept ones
marked — so the review issue shows what the writer could draw on, not only what it used."""

from __future__ import annotations

from collections import defaultdict

from pipeline.models import NewsItem


def sources_md(all_items: list[NewsItem], kept: list[NewsItem], max_per_source: int = 12) -> str:
    kept_urls = {i.url for i in kept}
    by_source: dict[str, list[NewsItem]] = defaultdict(list)
    for i in all_items:
        by_source[f"{i.source_type}: {i.source}"].append(i)
    out = [f"## Sources this week · {len(all_items)} items from {len(by_source)} sources, {len(kept)} kept for the writer\n"]
    out.append("| source | items | kept |\n|---|---|---|")
    for src, items in sorted(by_source.items(), key=lambda kv: -len(kv[1])):
        out.append(f"| {src} | {len(items)} | {sum(i.url in kept_urls for i in items)} |")
    out.append("\n<details><summary>Every item, by source (✅ = kept)</summary>\n")
    for src, items in sorted(by_source.items(), key=lambda kv: (kv[0].split(':')[0] != 'youtube', -len(kv[1]))):
        out.append(f"\n**{src}**")
        for i in sorted(items, key=lambda x: -x.score)[:max_per_source]:
            mark = "✅" if i.url in kept_urls else "·"
            out.append(f"- {mark} [{i.title.strip()[:110]}]({i.url}) — score {i.score:.1f}{', ' + i.track if i.track else ''}")
        if len(items) > max_per_source:
            out.append(f"- … {len(items) - max_per_source} more")
    out.append("\n</details>")
    return "\n".join(out)
