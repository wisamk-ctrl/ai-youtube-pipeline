"""English version (phase translate): marker integrity, the files it writes, and English passing
untouched through the Arabic-only voice, figure and caption handling. No network: the Anthropic
client is a fake, as in the other tests."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from pipeline.config import load_settings
from pipeline.language import apply_language, english_week, source_week, week_language
from pipeline.models import NewsItem
from pipeline.script_format import lint_voice, speakable, to_tts_text
from pipeline.scripting import translate
from pipeline.scripting.source_map import Attribution, SourceMap, claim_figures

ITEM = NewsItem(source="Reuters", source_type="rss", title="OpenAI raises $40 billion",
                summary="OpenAI raised $40 billion in a round led by SoftBank, Reuters reported.",
                url="https://example.com/openai-40bn", published=datetime(2026, 11, 3, tzinfo=timezone.utc))
SID = ITEM.id

AR = f"""[Section: المقدمة]
[Face]
أوبن إيه آي{{OpenAI}} جمعت أربعين مليار دولار. شو يعني هاد إلنا؟
[Pause]
[Visual: source {SID}]
حسب رويترز، الجولة قادتها سوفت بنك{{SoftBank}}.
[Visual: number 40 مليار | دولار جمعتها الشركة]
[On-Screen Text: أربعين مليار دولار]
[Visual: stock data center servers, blue light]
أهلا فيكم بأسبوع الذكاء الاصطناعي، معكم وسام.
[Pause 2s]"""

EN = f"""[Section: Intro]
[Face]
OpenAI just raised $40 billion. So what does that mean for us?
[Pause]
[Visual: source {SID}]
According to Reuters, the round was led by SoftBank.
[Visual: number $40 billion | raised by the company]
[On-Screen Text: $40 billion]
[Visual: stock data center servers, blue light]
Hi everyone, welcome to This Week in AI, I'm Wissam.
[Pause 2s]"""

PLAN = {"episode_title_ar": "أوبن إيه آي تجمع أربعين مليار", "cold_open_hook_en": "OpenAI raises $40bn",
        "segments": [{"track": "models", "item_ids": [SID], "headline_en": "OpenAI raises $40bn", "angle": "a",
                      "enterprise_impact": "e", "broll_ideas": [], "approx_seconds": 60}],
        "quick_fire_item_ids": [], "thumbnail_text_ar": "أربعين مليار"}


class FakeClient:
    """Streams the queued translations in order; answers parse() by the requested schema."""

    def __init__(self, translations):
        self.translations = list(translations)
        self.streams, self.parses = [], []
        self.messages = NS(stream=self._stream, parse=self._parse)

    def _stream(self, **kw):
        self.streams.append(kw)
        text = self.translations.pop(0)

        class S:
            def __enter__(s): return s
            def __exit__(s, *a): pass
            def get_final_message(s):
                return NS(stop_reason="end_turn", content=[NS(type="text", text=f"<script>\n{text}\n</script>")])
        return S()

    def _parse(self, **kw):
        fmt = kw["output_format"]
        self.parses.append(fmt.__name__)
        if fmt is translate.EnglishMeta:
            out = fmt(title="OpenAI raises $40 billion", description="What the round means.", thumbnail_text="$40 billion")
        elif fmt is translate.CritiqueEn:
            out = fmt(hook=9, clarity=8, pacing=8, flow=9, arabic=8, value=9,
                      worst_three=[translate.FixEn(where="So what does that", problem="p", fix="f")], verdict="Airable.")
        elif fmt is SourceMap:
            n = len(kw["messages"][0]["content"].split("<script_sentences>")[1].strip().splitlines())
            out = SourceMap(sentences=[Attribution(n=k, kind="claim" if k in (1, 3) else "transition",
                                                   item_ids=[SID] if k in (1, 3) else [],
                                                   support="direct" if k in (1, 3) else "none")
                                       for k in range(1, n + 1)])
        else:
            raise AssertionError(fmt)
        return NS(stop_reason="end_turn", parsed_output=out, usage=None)


def _week(tmp_path: Path, plan=PLAN) -> Path:
    src = tmp_path / "output" / "2026-W45"
    src.mkdir(parents=True)
    (src / "script.md").write_text(AR + "\n", encoding="utf-8")
    (src / "items.json").write_text(json.dumps([ITEM.to_dict()], ensure_ascii=False), encoding="utf-8")
    (src / "plan.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    return src


# ── marker integrity ──
def test_good_translation_passes_the_marker_check():
    assert translate.check(AR, EN) == []
    assert len(translate.markers(EN)) == len(translate.markers(AR)) == 8


@pytest.mark.parametrize("bad, why", [
    (EN.replace("[Pause]\n", "", 1), "markers changed"),
    (EN.replace(f"source {SID}", "source deadbeef00"), "markers changed"),
    (EN.replace("[Pause 2s]", "[Pause]"), "markers changed"),
    (EN.replace("[Face]", "[Visual: stock robot]"), "markers changed"),
    (EN.replace("$40 billion | raised", "$40 billion raised"), "markers changed"),
    (EN.replace("OpenAI just", "أوبن إيه آي just"), "Arabic text left"),
    (EN.replace("OpenAI just", "OpenAI{OpenAI} just"), "curly braces"),
    ("\n".join(ln for ln in EN.splitlines() if ln.startswith("[")) + "\nHi.", "cut short"),
])
def test_marker_check_refuses(bad, why):
    assert any(why in p for p in translate.check(AR, bad))


def test_translated_labels_and_titles_are_allowed():
    assert translate.check(AR, EN.replace("[Section: Intro]", "[Section: Opening]")) == []


def test_one_retry_then_success():
    client = FakeClient([EN.replace("[Pause]\n", "", 1), EN])
    out = translate.translate_script(AR, [ITEM], load_settings(), client)
    assert out == EN and len(client.streams) == 2
    assert "markers changed" in client.streams[1]["messages"][-1]["content"]


def test_two_bad_answers_fail_loudly():
    bad = EN.replace(f"source {SID}", "source other")
    with pytest.raises(translate.TranslationError, match="marker check twice"):
        translate.translate_script(AR, [ITEM], load_settings(), FakeClient([bad, bad]))


def test_prompt_carries_the_rules():
    s = translate._system(load_settings())
    for rule in ("enterprise leaders", "IT people", "never tell viewers to buy", "OpenAI", "no Arabic script",
                 "same order", "never changed", "This Week in AI"):
        assert rule in s


# ── the phase ──
def test_run_writes_the_english_week(tmp_path):
    src = _week(tmp_path)
    dst = tmp_path / "output" / "2026-W45-en"
    client = FakeClient([EN])
    summary = translate.run(src, dst, load_settings(), client)
    assert (dst / "script.md").read_text(encoding="utf-8").strip() == EN
    assert json.loads((dst / "items.json").read_text(encoding="utf-8"))[0]["url"] == ITEM.url
    plan = json.loads((dst / "plan.json").read_text(encoding="utf-8"))
    assert plan["language"] == "en" and plan["translated_from"] == "2026-W45"
    assert plan["episode_title_en"] == "OpenAI raises $40 billion" and plan["thumbnail_text_en"] == "$40 billion"
    assert plan["segments"] == PLAN["segments"]                       # the Arabic plan is kept for later phases
    crit = json.loads((dst / "critique.json").read_text(encoding="utf-8"))
    assert len(crit) == 1 and crit[0]["language"] == "en" and crit[0]["minimum"] == 8
    smap = (dst / "source_map.md").read_text(encoding="utf-8")
    assert "**0 unsourced claims**" in smap and "OpenAI just raised $40 billion" in smap
    assert summary["markers"] == 8 and client.parses == ["EnglishMeta", "CritiqueEn", "SourceMap"]


def test_existing_en_fields_are_reused(tmp_path):
    plan = {**PLAN, "episode_title_en": "Given title", "description_en": "Given.", "thumbnail_text_en": "Given"}
    src = _week(tmp_path, plan)
    client = FakeClient([EN])
    translate.run(src, tmp_path / "output" / "2026-W45-en", load_settings(), client)
    out = json.loads((tmp_path / "output" / "2026-W45-en" / "plan.json").read_text(encoding="utf-8"))
    assert out["episode_title_en"] == "Given title" and "EnglishMeta" not in client.parses


def test_english_critic_uses_the_english_rubric(tmp_path):
    client = FakeClient([])
    seen = {}
    orig = client._parse

    def spy(**kw):
        seen.update(kw)
        return orig(**kw)
    client.messages = NS(parse=spy)
    rec = translate.critique_en(EN, load_settings(), client)
    assert "English edition" in seen["system"] and "natural spoken English" in seen["system"]
    assert "Jordanian" not in seen["system"].split("<rubric>")[0]
    assert rec["scores"]["arabic"] == 8


def test_phase_translate_end_to_end(tmp_path, monkeypatch):
    import run_pipeline
    _week(tmp_path)
    monkeypatch.setattr(run_pipeline, "ROOT", tmp_path)
    monkeypatch.setattr(translate.anthropic, "Anthropic", lambda **kw: FakeClient([EN]))
    cfg = load_settings()
    out = tmp_path / "output" / "2026-W45"
    apply_language(cfg, out.name)
    run_pipeline.phase_translate(cfg, out)
    dst = tmp_path / "output" / "2026-W45-en"
    pack = (dst / "heygen_paste.md").read_text(encoding="utf-8")
    assert "e1412c8894c9462eb3aa8bc8ad1f6e26" in pack and "English clone" in pack
    assert "OpenAI just raised $40 billion" in pack
    assert (dst / "shotlist.md").exists()
    assert cfg["video"]["heygen"]["voice_id"] == "4c810d9c9906445f81dfd4f7d32259e0"   # the Arabic cfg is untouched


def test_translate_is_a_phase():
    src = Path(__file__).resolve().parents[1]
    assert '"translate"' in (src / "run_pipeline.py").read_text(encoding="utf-8")
    assert "translate]" in (src / ".github" / "workflows" / "weekly.yml").read_text(encoding="utf-8")


# ── language, voice, captions ──
def test_week_language_from_the_folder_name():
    assert week_language("2026-W45-en") == "en" and week_language("2026-W43-jo") == "ar"
    assert source_week("2026-W45-en") == "2026-W45" and english_week("2026-W45") == "2026-W45-en"
    assert english_week("2026-W45-en") == "2026-W45-en"


def test_english_week_uses_the_english_clone():
    cfg = apply_language(load_settings(), "2026-W45-en")
    h = cfg["video"]["heygen"]
    assert cfg["language"] == "en" and h["voice_id"] == "e1412c8894c9462eb3aa8bc8ad1f6e26"
    assert h["voice_id_ar"] == "4c810d9c9906445f81dfd4f7d32259e0"
    assert cfg["scripting"]["words_per_minute"] == cfg["scripting"]["words_per_minute_en"]
    ar = apply_language(load_settings(), "2026-W45")
    assert ar["language"] == "ar" and ar["video"]["heygen"]["voice_id"] == "4c810d9c9906445f81dfd4f7d32259e0"


def test_heygen_api_render_uses_the_english_clone(monkeypatch):
    from pipeline.video.heygen_client import HeyGenClient
    monkeypatch.setenv("HEYGEN_API_KEY", "k")
    monkeypatch.setenv("HEYGEN_VOICE_ID", "arabic-secret")
    monkeypatch.delenv("HEYGEN_VOICE_ID_EN", raising=False)
    assert HeyGenClient(apply_language(load_settings(), "2026-W45-en")).voice_id == "e1412c8894c9462eb3aa8bc8ad1f6e26"
    assert HeyGenClient(apply_language(load_settings(), "2026-W45")).voice_id == "arabic-secret"


def test_voice_pack_for_an_english_week():
    from pipeline.video import voicefirst
    cfg = apply_language(load_settings(), "2026-W45-en")
    chunks = voicefirst.pack(EN, cfg)
    text = " ".join(c["text"] for c in chunks)
    assert "OpenAI just raised $40 billion." in text and "SoftBank" in text
    assert "e1412c8894c9462eb3aa8bc8ad1f6e26" in voicefirst.pack_md(chunks, cfg, "2026-W45-en")


def test_english_passes_through_the_voice_text_unchanged():
    for text in ["Claude Code and G42 (the Abu Dhabi group) shipped GPT-6 Cyber.",
                 "AI agents (and that matters) are here.", "It's $40 billion, about 30%."]:
        assert speakable(text) == text                    # the real pronunciation map is loaded, and skipped
    assert to_tts_text("Claude is here. [Pause] (Really.)", "ellipsis") == "Claude is here. ... (Really.)"
    assert to_tts_text("Claude [Pause 2s] Code", "ssml") == 'Claude <break time="2.0s"/> Code'
    assert lint_voice(EN) == []
    assert speakable("مجموعة G42", {"G42": "جي فورتي تو"}) == "مجموعة جي فورتي تو"   # Arabic unchanged


def test_whisper_language_follows_the_week_folder(tmp_path, monkeypatch):
    from pipeline.post import subtitles
    seen = []

    class Model:
        def __init__(self, *a, **kw): pass
        def transcribe(self, path, language, **kw):
            seen.append(language)
            return [], NS(language=language, language_probability=1.0)
    monkeypatch.setitem(sys.modules, "faster_whisper", NS(WhisperModel=Model))
    for week in ("2026-W45-en", "2026-W45"):
        (tmp_path / week).mkdir()
        subtitles.transcribe_words(tmp_path / week / "talking_head.mp4", "tiny", cache=False)
    subtitles.transcribe_words(tmp_path / "2026-W45" / "talking_head.mp4", "tiny", cache=False, language="en")
    assert seen == ["en", "ar", "en"]


# ── source map on English ──
def test_english_figures_are_checked():
    assert claim_figures("It grew 30% to forty billion dollars, twenty-five firms.", "en") == ["30", "40", "25"]
    assert claim_figures("three point five billion", "en") == ["3.5"]
    assert claim_figures("One of the two biggest deals.", "en") == []         # not figures
    assert claim_figures("أربعين مليار") == ["40"]                             # Arabic default unchanged


def test_english_claim_with_an_unsourced_figure_is_flagged():
    from pipeline.scripting import source_map
    sents = ["OpenAI raised forty billion dollars.", "OpenAI raised seventy billion dollars."]
    smap = SourceMap(sentences=[Attribution(n=n, kind="claim", item_ids=[SID], support="direct") for n in (1, 2)])
    source_map.verify(sents, smap, [ITEM], "en")
    assert smap.sentences[0].support == "direct" and smap.sentences[1].support == "none"

