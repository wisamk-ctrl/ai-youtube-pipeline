"""Legal-risk flags for a script, read from its source map (founder 2026-11-20: "anything that puts us at legal
risk, we need to highlight"). Deterministic: word lists and source counts, no model call, so the same script
always gets the same flags.

  allegation  a breach, lawsuit, fraud, sanctions or similar claim about someone. Two outlets, or one tier-A
              outlet (a check), carry it; one weaker outlet is a major flag (W47: a breach blamed on Fireworks AI
              on a single security blog).
  advice      an imperative to buy, sell or invest. The channel never prescribes investments.
  sensitive   rulers, royals, religion or the state next to a negative claim (UAE Federal Decree-Law 34/2021 on
              rumours and cybercrime; Saudi equivalents). Mentioning them neutrally is fine.
  quote       words in quotation marks that the source map does not support directly.

legal.md sits next to source_map.md. A render refuses while it lists major flags, unless
reviewed/<week>/legal_ok.txt answers each one by its number, e.g. "(7) cut" or "(7) second source: …".
These are flags for the founder to judge, not legal advice.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from pipeline.models import NewsItem

ALLEGATION = re.compile(
    r"\b(breach\w*|hack\w*|fraud\w*|lawsuit|sue[sd]?|suing|accus\w*|alleg\w*|illegal\w*|sanction\w*|evad\w*|evasion|"
    r"smuggl\w*|brib\w*|scandal\w*|stole|stolen|theft|leak\w*|indict\w*|charged with|investigat\w*|fined|"
    r"cyberattack\w*|launder\w*)\b"
    r"|اختراق|اخترق|احتيال|دعوى|قضية ضد|رفع\w* قضية|متهم|اتهم|اتهام|غير قانوني|عقوبات|تهريب|رشوة|رشاوى|فضيحة|"
    r"تسريب|سرق|غرامة|تحقيق ب|هجوم إلكتروني|هجوم سيبراني|تبييض|غسيل أموال", re.I)
ADVICE = re.compile(
    r"\b(time to (buy|sell)|(you|we) should (buy|sell|invest)|buy (the|this|its|their) (stock|share)s?|"
    r"sell (the|this|your|its) (stock|share)s?|worth buying|a (good|great) investment|invest (in|now))\b"
    r"|اشتر[يو]ا?\b|اشتروا|بيعوا|استثمروا|لازم تستثمر|لازم تشتري|فرصة (شراء|استثمار)|وقت الشراء|وقت البيع", re.I)
POWER = re.compile(
    r"\b(crown prince|sheikh|emir|king|royal family|ruler|islam\w*|religio\w*|the prophet)\b"
    r"|ولي العهد|الشيخ|الأمير|الملك|سمو|الأسرة الحاكمة|حاكم|الإسلام|الدين|النبي|الرسول", re.I)
NEGATIVE = re.compile(
    r"\b(fail\w*|criticis\w*|criticiz\w*|corrupt\w*|abus\w*|condemn\w*|reject\w*|blam\w*|repress\w*)\b"
    r"|فشل|فشلت|انتقد|انتقاد|فساد|انتهاك|أدان|رفض|قمع|لام", re.I)
SPEECH = re.compile(r"\b(said|says|say|called|calls|described|told|warned|quoted)\b|قال|وصف|حكى|صرّح|صرح|حذّر|حذر", re.I)
QUOTE = re.compile(r"«[^»]{3,}»|“[^”]{3,}”|\"[^\"]{3,}\"")
_ROW = re.compile(r"^\| (\d+) \| (.*) \| (\w+) \| (\w+) \| (.*) \|\s*$")
_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
_COUNT = re.compile(r"\*\*(\d+) major legal flag")


@dataclass(frozen=True)
class Flag:
    n: int
    severity: str          # major | check
    rule: str              # allegation | advice | sensitive | quote
    sentence: str
    why: str


def _rows(source_map_md: str):
    for line in source_map_md.splitlines():
        m = _ROW.match(line)
        if m:
            yield int(m.group(1)), m.group(2), m.group(3), m.group(4), _LINK.findall(m.group(5))


def check(source_map_md: str, items: list[NewsItem]) -> list[Flag]:
    from pipeline.ingestion.publishers import load_publishers
    pubs = load_publishers()
    tier = {i.url: pubs.tier(i) for i in items}
    flags: list[Flag] = []
    for n, sent, kind, support, links in _rows(source_map_md):
        outlets = {name for name, _ in links}
        tier_a = any(tier.get(url) == "A" for _, url in links)
        if ADVICE.search(sent):
            flags.append(Flag(n, "major", "advice", sent, "reads as an instruction to buy, sell or invest"))
        if POWER.search(sent) and (NEGATIVE.search(sent) or ALLEGATION.search(sent)):
            flags.append(Flag(n, "major", "sensitive", sent, "a ruler, royal, religion or the state next to a negative claim"))
        if kind != "claim":                 # greetings, transitions, questions, views: only advice/sensitivity apply
            continue
        if ALLEGATION.search(sent) and len(outlets) < 2:
            if tier_a and support == "direct":
                flags.append(Flag(n, "check", "allegation", sent, f"one wire/primary source ({', '.join(outlets)})"))
            else:
                flags.append(Flag(n, "major", "allegation", sent,
                                  f"claim against someone on {len(outlets)} outlet(s), none tier A with direct support"))
        quotes = [q.strip('«»“”"') for q in QUOTE.findall(sent)]
        if quotes and support != "direct":
            # A name or term in quotation marks (a programme, a product: ≤ 5 words) is a check; real quoted
            # speech is major (W47-en: SDAIA's "Year of AI" was blocked as a quote).
            short = all(len(q.split()) <= 5 for q in quotes) and not SPEECH.search(sent)
            flags.append(Flag(n, "check" if short else "major", "quote", sent,
                              f"quoted words, source support is '{support}'"))
    return flags


def render_md(flags: list[Flag]) -> str:
    major = [f for f in flags if f.severity == "major"]
    if not flags:
        return "# Legal flags\n\n✅ No legal flags.\n"
    lines = ["# Legal flags", "", f"**{len(major)} major legal flag(s)** · {len(flags) - len(major)} to check", "",
             "Flags for the editor, not legal advice. A major flag blocks the render until "
             "reviewed/<week>/legal_ok.txt answers it by number.", ""]
    for f in sorted(flags, key=lambda f: (f.severity != "major", f.n)):
        lines.append(f"- ({f.n}) [{f.severity}] {f.rule} — {f.sentence} — _{f.why}_")
    return "\n".join(lines) + "\n"


def majors_in_md(md: str) -> tuple[int, list[str]]:
    m = _COUNT.search(md)
    nums = re.findall(r"^- \((\d+)\) \[major\]", md, re.M)
    return (int(m.group(1)) if m else 0), [f"({n})" for n in nums]


def write(out: Path, items: list[NewsItem]) -> str:
    """legal.md from the week's source_map.md; returns a one-line summary for the log."""
    smap = out / "source_map.md"
    if not smap.exists():
        return "no source map: legal flags not checked"
    flags = check(smap.read_text(encoding="utf-8"), items)
    (out / "legal.md").write_text(render_md(flags), encoding="utf-8")
    major = sum(f.severity == "major" for f in flags)
    return f"{major} major legal flag(s), {len(flags) - major} to check"


def gate(out: Path, root: Path | None = None) -> tuple[bool, str]:
    """May this week be rendered? Refuses while legal.md lists major flags not answered in legal_ok.txt."""
    from pipeline.config import ROOT
    path = out / "legal.md"
    if not path.exists():
        return True, "no legal.md: legal flags were not checked for this week"
    count, nums = majors_in_md(path.read_text(encoding="utf-8"))
    if count == 0:
        return True, "no major legal flags"
    note = (root or ROOT) / "reviewed" / out.name / "legal_ok.txt"
    answered = note.read_text(encoding="utf-8") if note.exists() else ""
    missing = [n for n in nums if n not in answered]
    if not missing:
        return True, f"{count} major legal flag(s), each answered in {note}"
    return False, (f"Refusing: {len(missing)} major legal flag(s) unanswered: {', '.join(missing)} (see {path}). "
                   f"Fix the script, or answer each by number in {note}.")
