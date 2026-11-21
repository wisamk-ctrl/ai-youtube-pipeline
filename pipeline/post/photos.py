"""Real photos and generated clips (founder 2026-11-20: "real photos of individuals related to the companies… and
more animations… digital, then real, then digital").

photo      [Visual: photo <subject>] — a real photo of a named person, building or product from Wikimedia Commons,
           taken only under a licence that allows reuse with credit (CC0, public domain, CC BY, CC BY-SA). The
           author and licence go into the episode's credits. No such photo: a title card with the subject's name.
           Never news-agency or press photos (rights unknown), never a generated likeness of a real person.
generated  [Visual: generated <scene>] — a clip we generate (HeyGen video, Higgsfield models): concept scenes only,
           no real person, logo or event. Made by the founder from the generation pack in the Review issue and
           listed in reviewed/<week>/visuals.yaml; until then the scene text is searched as stock.
"""
from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

import requests

API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "news-explainer-pipeline/1.0 (editorial photo search)"}
_REUSABLE = re.compile(r"^(cc0|public domain|pd\b.*|cc[ -]by(-sa)?[ -]\d(\.\d)?.*)$", re.I)
_NOT_OK = re.compile(r"\b(nc|nd|non-?commercial|no ?deriv|fair use|all rights reserved)\b", re.I)
DIGITAL, REAL = ("stock", "generated"), ("photo",)


def reusable(licence: str) -> bool:
    lic = (licence or "").strip()
    return bool(_REUSABLE.match(lic)) and not _NOT_OK.search(lic)


def _text(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value or "")).strip()


_GENERIC = {"headquarters", "hq", "head", "office", "offices", "campus", "building", "tower", "towers", "center",
            "centre", "the", "of", "in", "at", "and", "photo", "portrait"}


def _name_words(subject: str) -> list[str]:
    """The words of the subject before its first generic word: "OpenAI headquarters" → ["openai"]; a person's name
    → all of it. A photo's file title must contain every one of them (2026-11-21: "OpenAI headquarters" matched
    the European Southern Observatory)."""
    out = []
    for w in re.findall(r"[\w']+", subject.lower()):
        if w in _GENERIC:
            break
        out.append(w)
    return out


def _get(http, params, tries: int = 4):
    import time
    for n in range(tries):
        r = http.get(API, timeout=30, headers=UA, params=params)
        if getattr(r, "status_code", 200) != 429 or n == tries - 1:
            r.raise_for_status()
            return r.json()
        time.sleep(5 * (n + 1))               # Commons asks clients to back off


def commons_search(subject: str, min_width: int = 1200, http=requests, avoid: set[str] | None = None) -> dict[str, Any] | None:
    """The first Commons photo of `subject` under a reusable licence, as a credit-ready dict, or None.
    `File:<name>` names one exact file. Files in `avoid` (used in earlier episodes) are skipped."""
    base = {"action": "query", "format": "json", "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": 1920}
    exact = subject.startswith("File:")
    params = {**base, "titles": subject} if exact else \
        {**base, "generator": "search", "gsrnamespace": 6, "gsrlimit": 25, "gsrsearch": f"{subject} filetype:bitmap"}
    data = _get(http, params) or {}
    pages = sorted((data.get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    need = [] if exact else _name_words(subject)
    for p in pages:
        title = p.get("title", "")
        if title in (avoid or set()) or not all(w in title.lower() for w in need):
            continue
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        lic = _text((meta.get("LicenseShortName") or {}).get("value", ""))
        if not reusable(lic) or (info.get("width") or 0) < min_width:
            continue
        return {"provider": "Wikimedia Commons", "title": title, "license": lic,
                "author": _text((meta.get("Artist") or {}).get("value", "")) or "unknown",
                "url": info.get("descriptionurl", ""), "file": info.get("thumburl") or info.get("url", "")}
    return None


def fetch_photo(subject: str, cache: Path, http=requests, avoid: set[str] | None = None) -> tuple[Path, dict[str, Any]] | None:
    found = commons_search(subject, http=http, avoid=avoid)
    if not found or not found["file"]:
        return None
    cache.mkdir(parents=True, exist_ok=True)
    dest = cache / (re.sub(r"[^\w]+", "_", found["title"])[:80] + Path(found["file"].split("?")[0]).suffix)
    if not dest.exists():
        img = http.get(found["file"], timeout=60, headers=UA)
        img.raise_for_status()
        dest.write_bytes(img.content)
    return dest, found


def generation_pack(shots: list, own: dict[str, list[str]]) -> str:
    """The generated shots still without a clip, as prompts the founder can run (HeyGen, Higgsfield)."""
    todo, seen = [], set()
    for s in shots:
        key = " ".join(s.payload.lower().split())
        if s.kind == "generated" and key not in own and key not in seen:
            seen.add(key)
            todo.append(s.payload)
    if not todo:
        return ""
    lines = ["Generated clips to make (16:9, 5–8 s, no real person, logo or readable text; tech/AI house look):", ""]
    lines += [f"{n}. {p}" for n, p in enumerate(todo, 1)]
    lines += ["", "Then commit reviewed/<week>/visuals.yaml with each prompt as a key and the clip's link as its value. "
              "Until a clip is listed, the shot uses stock footage for the same words."]
    return "\n".join(lines)


def variety_notes(shots: list) -> list[str]:
    """Shot-list notes: a stock search used more than once, and long runs of digital shots with no real one."""
    notes, counts = [], {}
    for s in shots:
        if s.kind == "stock":
            key = " ".join(s.payload.lower().split())
            counts[key] = counts.get(key, 0) + 1
    notes += [f"stock search «{k}» used {n} times" for k, n in counts.items() if n > 1]
    run, longest, has_real = 0, 0, False
    for s in shots:
        if s.kind in DIGITAL:
            run += 1
            longest = max(longest, run)
        elif s.kind in REAL:
            has_real, run = True, 0
    if not has_real and longest:
        notes.append("no real photo shots (aim for one per story with a named person or company)")
    elif longest > 2:
        notes.append(f"{longest} digital shots in a row before a real one (aim for no more than 2)")
    return notes
