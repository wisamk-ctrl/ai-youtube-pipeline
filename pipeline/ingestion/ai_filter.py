"""
AI relevance filter for broad tech and business outlets (founder 2026-11-22: more regional coverage).

Regional outlets such as Arabian Business, Gulf News or Asharq Al-Awsat publish everything from
oil to football. A source flagged `ai_only: true` in config/settings.yaml (rss_feeds or
google_news_sites) only passes the items this filter calls AI news, so the rest never reaches scoring.

An item is AI news when its headline names AI (English, Arabic or Turkish), or when its body does
at least twice: one passing "fintech, AI and healthcare" in a body is not an AI story.
"""

from __future__ import annotations

import re

# Arabic short vowels, shadda, sukun, dagger alef, and tatweel: removed before matching.
_ARABIC_MARKS = re.compile(r"[ً-ْٰـ]")

# "AI" only in capitals and as its own token: not "Ai Weiwei", not the flight code "AI171".
_AI_TOKEN = re.compile(r"(?<![\w.])A\.?I(?![\w])")

_TERMS = re.compile("|".join([
    # English
    r"\bartificial intelligence\b", r"\bmachine learning\b", r"\bdeep learning\b", r"\bneural net",
    r"\blarge language models?\b", r"\bLLMs?\b", r"\bgen-?ai\b", r"\bgenerative\b", r"\bchatbots?\b",
    r"\bchat ?gpt\b", r"\bgpt-?\d", r"\bopenai\b", r"\banthropic\b", r"\bdeepmind\b", r"\bdeepseek\b",
    r"\bnvidia\b", r"\bsemiconductors?\b", r"\bgpus?\b", r"\bdata ?cent(?:er|re)s?\b", r"\bagentic\b",
    r"\bcomputer vision\b", r"\bfacial recognition\b",
    # Gulf AI names (Falcon is left out: it is also the bird)
    r"\bg42\b", r"\bcore42\b", r"\bmbzuai\b", r"\bhumain\b", r"\bsdaia\b", r"\bjais\b",
    # Arabic: no word boundaries, because prefixes (بـ، لـ، و، ال) attach to the word
    r"ذكاء\s*(?:ال)?[اإأ]?صطناع[يى]", r"ذكاء\s*(?:ال)?صناع[يى]",
    r"تعلم\s*(?:ال)?[آا]ل[ةهيى]", r"تعلم\s*(?:ال)?عميق",
    r"نموذج\w*\s+(?:ال)?لغوي", r"نماذج\s+(?:ال)?لغوي",
    r"روبوت(?:ات)?\s*(?:ال)?(?:محادثة|دردشة)", r"شات\s*جي\s*بي\s*تي",
    r"[أا]وبن\s*[إا]يه?\s*[آا]ي", r"[أا]نثروبيك", r"[إا]نفيديا",
    r"مراكز\s*(?:ال)?بيانات", r"مركز\s*(?:لل)?بيانات", r"[أا]شباه\s*(?:ال)?موصلات",
    # Turkish
    r"\byapay\s+zek[aâ]", r"\bmakine\s+öğren", r"\bderin\s+öğren", r"\bbüyük\s+dil\s+model",
    r"\bsohbet\s+robot", r"\bveri\s+merkez",
]), re.IGNORECASE)


def _hits(text: str) -> int:
    text = _ARABIC_MARKS.sub("", text or "")
    return len(_AI_TOKEN.findall(text)) + len(_TERMS.findall(text))


def is_ai_relevant(title: str, summary: str = "") -> bool:
    """True when the headline names AI, or the body does at least twice."""
    return _hits(title) > 0 or _hits(summary) >= 2
