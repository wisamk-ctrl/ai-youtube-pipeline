"""
Episode language, read from the week folder's name.

The English version of a week lives next to the Arabic one: output/2026-W45 is Arabic,
output/2026-W45-en is English (made by the `translate` phase from the Arabic week's directed
script). Every phase that needs to know the language — the voice, Whisper, the voice text —
derives it from the folder name, so no extra flag has to be passed around.
"""

from __future__ import annotations

from typing import Any

EN_SUFFIX = "-en"


def week_language(week: str) -> str:
    """'en' for a week folder ending in -en, else 'ar'."""
    return "en" if str(week).endswith(EN_SUFFIX) else "ar"


def source_week(week: str) -> str:
    """The Arabic week an English week was translated from: '2026-W45-en' → '2026-W45'."""
    return week[: -len(EN_SUFFIX)] if week.endswith(EN_SUFFIX) else week


def english_week(week: str) -> str:
    return week if week.endswith(EN_SUFFIX) else week + EN_SUFFIX


def apply_language(cfg: dict[str, Any], week: str) -> dict[str, Any]:
    """Set cfg['language'] for this week and, for an English week, swap in the English voice
    clone (video.heygen.voice_id_en / voice_name_en), so the paste pack, the API render and the
    voice pack all use it without each knowing about languages; scripting.words_per_minute becomes
    words_per_minute_en (English pace, for shot timings). Returns cfg (changed in place)."""
    lang = week_language(week)
    cfg["language"] = lang
    s = cfg.get("scripting")
    if lang == "en" and isinstance(s, dict) and s.get("words_per_minute_en"):
        s["words_per_minute"] = s["words_per_minute_en"]
    h = cfg.get("video", {}).get("heygen")
    if lang == "en" and isinstance(h, dict) and h.get("voice_id_en"):
        h.setdefault("voice_id_ar", h.get("voice_id"))
        h["voice_id"] = h["voice_id_en"]
        h["voice_name"] = h.get("voice_name_en") or f"your English voice clone ({h['voice_id_en']})"
    return cfg
