"""
Tashkeel (diacritics) pass before TTS — style guide §6.

Arabic speech engines mispronounce passive verbs, unfamiliar proper names and words with more
than one reading. Full diacritisation confuses some engines and lengthens audio, so this pass
adds vowel marks ONLY where the style guide says: ambiguous words, passives, foreign names, and
the last word before a [Pause]. Production markers and Latin text are passed through untouched.

Runs on the approved script, writes script.tashkeel.md next to it, and the TTS text is built
from that file. Off by default until a voice test confirms the engine honours the marks
(`video.tashkeel: true`).
"""

from __future__ import annotations

import logging
import re
from typing import Any

import anthropic
from pydantic import BaseModel, Field

from pipeline import usage
from pipeline.script_format import MARKER_RE

log = logging.getLogger(__name__)

HARAKAT_RE = re.compile(r"[ً-ْٰ]")

SYSTEM = """You prepare Arabic broadcast scripts for a speech engine. Add diacritics (tashkeel) ONLY where
a careful presenter would need them to avoid a misreading. Scripts are in Jordanian colloquial Arabic:
never add MSA case endings to colloquial words; mark only what a speech engine would misread:
- passive verbs (أُعلِن، تُدار، يُطلَق)
- words with more than one common reading (عَلِم/عِلْم، قَدَّم/قَدِم، سَبَق/سُبُق)
- unfamiliar proper names transliterated into Arabic (هِينا فِيركونين، مُون شوت)
- case endings on the last word before a pause marker when it affects pronunciation
Do NOT fully vocalise. Do NOT change, add, remove or reorder any word. Keep every production marker
in square brackets, every Latin word and every number exactly as given. Return the full script."""


class Vocalised(BaseModel):
    script: str = Field(description="The same script with sparse tashkeel added")


def _stats(text: str) -> tuple[int, int]:
    words = [w for w in re.sub(MARKER_RE, " ", text).split() if re.search(r"[؀-ۿ]", w)]
    marked = sum(1 for w in words if HARAKAT_RE.search(w))
    return marked, len(words)


def strip_harakat(text: str) -> str:
    return HARAKAT_RE.sub("", text)


def vocalise(script: str, cfg: dict[str, Any], client: anthropic.Anthropic | None = None) -> str:
    """Return the script with sparse diacritics. Refuses the result if any word changed."""
    client = client or anthropic.Anthropic(max_retries=3)
    model = cfg["video"].get("tashkeel_model") or cfg["scripting"].get("aux_model", cfg["scripting"]["model"])
    resp = client.messages.parse(model=model, max_tokens=16000, system=SYSTEM,
                                 messages=[{"role": "user", "content": script}], output_format=Vocalised)
    usage.record("tashkeel", model, getattr(resp, "usage", None))
    if resp.stop_reason != "end_turn" or resp.parsed_output is None:
        raise RuntimeError(f"tashkeel stopped early: {resp.stop_reason}")
    out = resp.parsed_output.script
    if strip_harakat(out).split() != strip_harakat(script).split():
        raise ValueError("tashkeel pass changed the words, not only the marks — refusing it")
    marked, total = _stats(out)
    before, _ = _stats(script)
    log.info("Tashkeel: %d/%d Arabic words marked (was %d)", marked, total, before)
    return out
