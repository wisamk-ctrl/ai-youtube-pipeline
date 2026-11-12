"""YouTube package, offline: chapters, description, localizations, caption upload (mocked API),
Shorts span picker, thumbnail / end card / Shorts HTML, disclosure lower-third, timeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.post import packaging, shorts  # noqa: E402
from pipeline.post.overlays import Card, disclosure_card  # noqa: E402
from pipeline.post.subtitles import Word, script_captions, write_srt  # noqa: E402
from pipeline.publish import description as desc  # noqa: E402
from pipeline.publish import youtube_upload as yu  # noqa: E402
from pipeline.script_format import Cue, spoken_text, spoken_words, unbraced  # noqa: E402

CFG = {"scripting": {"words_per_minute": 130, "channel_name": "أسبوع الذكاء الاصطناعي"},
       "publish": {"privacy": "unlisted", "publish_weekday": 6, "publish_hour_utc": 6, "tags": ["AI"],
                   "hashtags": ["#AI"]},
       "post": {}, "visuals": {}}


def _sentence(word: str, n: int = 10) -> str:
    words = [f"{word}{chr(0x0628 + j)}" for j in range(n)]       # distinct words: probes match once
    return " ".join(words[:-1] + [words[-1] + "."])


def _script() -> str:
    """Cold open, three stories (each ~100 words ≈ 40 s at 0.4 s a word), a quick-fire round, outro."""
    parts = ["[Section: الافتتاحية]\n" + " ".join(_sentence(f"افتتاح{k}", 8) for k in range(3))]
    for s, name in enumerate(("نموذج جديد من ميسترال", "وكلاء الذكاء", "رقائق الاستدلال")):
        parts.append(f"[Section: {name}]\n" + " ".join(_sentence(f"قصة{s}كلمة{k}") for k in range(10)))
    parts.append("[Section: أخبار سريعة]\n" + " ".join(_sentence(f"سريع{k}") for k in range(8)))
    parts.append("[Section: الختام]\n" + _sentence("وداعا", 8))
    return "\n\n".join(parts)


def _srt(tmp_path: Path, script: str, step: float = 0.4) -> Path:
    toks = [unbraced(t) for t in spoken_words(spoken_text(script))]
    heard = [Word(i * step, i * step + step * 0.9, " " + w) for i, w in enumerate(toks)]
    return write_srt(script_captions(spoken_text(script), heard), tmp_path / "subtitles.srt")


# ── Chapters ────────────────────────────────────────────────────────────────
def test_chapters_first_at_zero_and_three_minimum():
    ch = desc.chapters([("الافتتاحية", 3.0), ("قصة", 40.0), ("خبر", 95.0)], duration=200)
    assert [t for t, _ in ch] == [0.0, 40.0, 95.0]
    assert desc.chapter_lines(ch)[0] == "00:00 الافتتاحية" and desc.chapter_lines(ch)[2] == "01:35 خبر"
    assert desc.chapters([("a", 0), ("b", 60)], duration=200) == []          # fewer than 3: none


def test_chapters_drop_short_ones_and_short_tail():
    ch = desc.chapters([("a", 0), ("b", 30), ("c", 34), ("d", 90), ("e", 195)], duration=200)
    assert ch == [(0.0, "a"), (34.0, "c"), (90.0, "d")]        # b (4 s) gives way to c; e is 5 s before the end
    assert desc.chapters([("a", 0), ("b", 5), ("c", 9)], duration=100) == []
    assert desc.fmt_time(3725) == "1:02:05"


def test_description_has_hook_chapters_sources_credits_disclaimer():
    script = _script()
    plan = {"episode_title_ar": "عنوان", "cold_open_hook_en": "English hook", "segments": [{"headline_en": "Eng"}]}
    sections = [("الافتتاحية", 0.0), ("نموذج جديد", 30.0), ("وكلاء", 75.0), ("الختام", 150.0)]
    text = desc.build_description(plan, [{"title": "Mistral <b>Large</b>", "url": "https://mistral.ai/news/x"}], CFG,
                                  sections=sections, duration=180, script=script,
                                  credits=[{"provider": "pixabay", "author": "Ann"}, {"provider": "pixabay", "author": "Bo"}])
    assert text.startswith("افتتاح0")                      # the approved cold open, not the English hook
    assert "English hook" not in text and "Eng\n" not in text
    assert "00:00 الافتتاحية\n00:30 نموذج جديد\n01:15 وكلاء\n02:30 الختام" in text
    assert "- Mistral bLarge/b: https://mistral.ai/news/x" in text and "<" not in text and ">" not in text
    assert "Pixabay (Ann، Bo)" in text
    assert "ليس نصيحة استثمارية" in text and "بموافقة وسام" in text and text.rstrip().endswith("#AI")


def test_description_without_valid_chapters_lists_headlines():
    text = desc.build_description({"segments": []}, [], CFG, sections=[("الافتتاحية", 0), ("قصة", 4), ("الختام", 8)])
    assert "00:00" not in text and "• قصة" in text


def test_description_trims_sources_not_disclaimer():
    many = [{"title": "t" * 200, "url": f"https://reuters.com/{k}"} for k in range(60)]
    text = desc.build_description({"segments": []}, many, CFG)
    assert len(text) <= 5000 and "ليس نصيحة استثمارية" in text and "#AI" in text


def test_sources_prefer_cited_and_tier_ab(tmp_path):
    items = [{"id": "a", "source": "Reuters", "source_type": "rss", "title": "R", "summary": "", "url": "https://www.reuters.com/x",
              "published": "2026-11-01T00:00:00+00:00"},
             {"id": "b", "source": "Some Blog", "source_type": "rss", "title": "S", "summary": "", "url": "https://shattered.io/y",
              "published": "2026-11-01T00:00:00+00:00"},
             {"id": "c", "source": "Mail", "source_type": "rss", "title": "M", "summary": "", "url": "mailto:x@y",
              "published": "2026-11-01T00:00:00+00:00"}]
    (tmp_path / "source_map.md").write_text("| 1 | s | claim | direct | [Reuters](https://www.reuters.com/x); [Blog](https://shattered.io/y) |",
                                           encoding="utf-8")
    got = desc.pick_sources(tmp_path, {"segments": [{"item_ids": ["a", "b", "c"]}]}, items)
    assert [g["id"] for g in got] == ["a"]             # tier C dropped while a tier A/B source exists


# ── Localizations ───────────────────────────────────────────────────────────
def test_localizations_payload():
    plan = {"episode_title_ar": "ع", "cold_open_hook_en": "Hook", "segments": [{"headline_en": "Mistral ships"}]}
    loc = desc.localizations(plan, [{"title": "R", "url": "https://r.com"}], CFG)
    assert loc["en"]["title"] == "AI Week (Arabic): Mistral ships"
    assert "Hook" in loc["en"]["description"] and "https://r.com" in loc["en"]["description"]
    assert desc.localizations({"episode_title_ar": "ع", "segments": []}, [], CFG) == {}
    assert desc.localizations(dict(plan, episode_title_en="The week"), [], CFG)["en"]["title"] == "The week"
    body = yu.video_body(plan, "d", CFG, yu.next_publish_time(CFG), loc)
    assert body["localizations"] == loc and body["snippet"]["defaultLanguage"] == "ar"
    assert body["status"]["containsSyntheticMedia"] is True


# ── Upload (mocked client) ──────────────────────────────────────────────────
def _yt(ids=("vid1",)):
    yt = MagicMock()
    yt.videos.return_value.insert.return_value.next_chunk.side_effect = [(None, {"id": i}) for i in ids]
    yt.captions.return_value.insert.return_value.execute.return_value = {"id": "cap1"}
    return yt


def _week(tmp_path: Path) -> Path:
    (tmp_path / "final_subtitled.mp4").write_bytes(b"\0" * 1024)
    (tmp_path / "thumbnail.png").write_bytes(b"\x89PNG")
    (tmp_path / "plan.json").write_text(json.dumps({"episode_title_ar": "عنوان الحلقة", "cold_open_hook_en": "Hook",
                                                    "segments": [{"item_ids": [], "headline_en": "H"}]}), encoding="utf-8")
    (tmp_path / "items.json").write_text("[]", encoding="utf-8")
    (tmp_path / "script.md").write_text(_script(), encoding="utf-8")
    (tmp_path / "subtitles.srt").write_text("1\n00:00:00,000 --> 00:00:02,000\nا\n", encoding="utf-8")
    (tmp_path / "subtitles.final.srt").write_text("1\n00:00:00,000 --> 00:00:02,000\nب\n", encoding="utf-8")
    (tmp_path / "timeline.json").write_text(json.dumps({"sections": [{"title": "الافتتاحية", "start": 0},
                                                                    {"title": "قصة", "start": 40}, {"title": "الختام", "start": 120}],
                                                       "duration": 200}), encoding="utf-8")
    return tmp_path


def test_run_publish_uploads_captions_thumbnail_localizations(tmp_path):
    out = _week(tmp_path)
    yt = _yt()
    assert yu.run_publish(out, CFG, yt=yt) == "vid1"
    kw = yt.videos.return_value.insert.call_args.kwargs
    assert kw["part"] == "snippet,status,localizations" and "en" in kw["body"]["localizations"]
    assert "00:40 قصة" in kw["body"]["snippet"]["description"]
    cap = yt.captions.return_value.insert.call_args.kwargs
    assert cap["part"] == "snippet"
    assert cap["body"]["snippet"] == {"videoId": "vid1", "language": "ar", "name": "العربية", "isDraft": False}
    assert cap["media_body"]._filename.endswith("subtitles.final.srt")       # shifted for the sting
    assert yt.thumbnails.return_value.set.call_args.kwargs["videoId"] == "vid1"
    assert (out / "description.txt").exists() and json.loads((out / "youtube.json").read_text())["shorts"] == []


def test_caption_failure_is_not_fatal(tmp_path):
    srt = tmp_path / "s.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nا\n", encoding="utf-8")
    yt = MagicMock()
    yt.captions.return_value.insert.return_value.execute.side_effect = RuntimeError("insufficientPermissions")
    assert yu.upload_captions(yt, "v", srt) is None


def test_shorts_upload_only_when_enabled(tmp_path):
    out = _week(tmp_path)
    (out / "shorts").mkdir()
    (out / "shorts" / "short_01.mp4").write_bytes(b"\0" * 512)
    (out / "shorts" / "shorts.json").write_text(json.dumps([{"file": "short_01.mp4", "title": "وكلاء الذكاء",
                                                            "start": 30, "end": 70, "episode_start": 47}]), encoding="utf-8")
    yt = _yt()
    yu.run_publish(out, CFG, yt=yt)
    assert yt.videos.return_value.insert.call_count == 1                     # off by default
    cfg = json.loads(json.dumps(CFG))
    cfg["publish"]["shorts"] = {"enabled": True}
    yt = _yt(("vid1", "s1"))
    yu.run_publish(out, cfg, yt=yt)
    body = yt.videos.return_value.insert.call_args_list[1].kwargs["body"]
    assert body["snippet"]["title"] == "وكلاء الذكاء #Shorts"
    assert "https://youtu.be/vid1?t=47" in body["snippet"]["description"] and "#Shorts" in body["snippet"]["description"]
    assert json.loads((out / "youtube.json").read_text())["shorts"][0]["video_id"] == "s1"


# ── Shorts picker ───────────────────────────────────────────────────────────
def test_pick_spans_one_story_each_sentence_aligned(tmp_path):
    script = _script()
    srt = _srt(tmp_path, script)
    spans = shorts.pick_spans(script, srt)
    assert [s.title for s in spans] == ["نموذج جديد من ميسترال", "وكلاء الذكاء", "رقائق الاستدلال"]
    starts = {round(t, 2) for t, _ in __import__("pipeline.post.overlays", fromlist=["_srt_index"])._srt_index(srt)}
    for s in spans:
        assert 30 <= s.end - s.start <= 58 and s.start in starts            # starts on a caption = a sentence start
    # Story 1 starts after the cold open's 24 words; ends at a sentence end inside its own section (100 words).
    assert spans[0].start == round(24 * 0.4, 2) and spans[0].end <= (24 + 100) * 0.4


def test_pick_spans_skips_short_sections_and_needs_captions(tmp_path):
    script = "[Section: الافتتاحية]\n" + _sentence("ا") + "\n[Section: قصة قصيرة]\n" + _sentence("ب") + "\n[Section: الختام]\n" + _sentence("ج")
    assert shorts.pick_spans(script, _srt(tmp_path, script)) == []
    assert shorts.pick_spans(_script(), None) == []


def test_short_srt_is_shifted_and_clipped(tmp_path):
    srt = _srt(tmp_path, _script())
    sub = shorts._short_srt(srt, 9.6, 30.0, tmp_path / "s.srt").read_text(encoding="utf-8").replace("\u2068", "").replace("\u2069", "")
    assert sub.startswith("1\n00:00:00,000 --> ") and "قصة0كلمة0" in sub and "افتتاح" not in sub


def test_shorts_layout_varies():
    g1 = shorts.filter_graph(40, 656, None, "Noto Naskh Arabic")
    assert "boxblur" in g1 and "overlay=0:656" in g1 and "tpad=stop_mode=clone:stop_duration=2.0" in g1
    assert "gte(t,40.000)" in g1
    htmls = {shorts.title_html("وكلاء", v, 656) for v in shorts.VARIANTS}
    assert len(htmls) == len(shorts.VARIANTS) and 'dir="rtl"' in next(iter(htmls))
    assert "الحلقة الكاملة على القناة" in shorts.end_html("أسبوع الذكاء الاصطناعي")


# ── Cards ───────────────────────────────────────────────────────────────────
def test_thumbnail_html_builds():
    h = packaging.thumbnail_html("سباق الرقائق الجديد", "أسبوع الذكاء الاصطناعي", b"\xff\xd8jpeg")
    assert 'dir="rtl"' in h and "سباق الرقائق <b>الجديد</b>" in h and "data:image/jpeg;base64," in h
    assert "width:1280px" in h.replace(" ", "") and "#E8B24A" in h
    assert "<img" not in packaging.thumbnail_html("كلمتين فقط", "s")


def test_thumbnail_skipped_without_text(tmp_path):
    (tmp_path / "plan.json").write_text("{}", encoding="utf-8")
    assert packaging.render_thumbnail(tmp_path, CFG) is None


def test_end_card_html_and_setting(tmp_path):
    h = packaging.end_card_html("أسبوع الذكاء الاصطناعي")
    assert "اشترك" in h and "أسبوع الذكاء الاصطناعي" in h
    assert packaging.end_card({"post": {"end_card": {"enabled": False}}}, tmp_path) is None


def test_disclosure_card_first_minute_and_clear_of_cards(tmp_path):
    other = Card(Cue("onscreen", "x", 0, 3.0), 3.0, 6.0, tmp_path / "c.png")
    d = disclosure_card([other], {}, tmp_path)
    assert d.cue.text == "توأم رقمي لوسام — بموافقة وسام" and d.at == 9.5 and d.at + d.seconds <= 60
    assert disclosure_card([], {"enabled": False}, tmp_path) is None
    late = [Card(Cue("onscreen", "x", 0, t), t, 6.0, tmp_path / "c.png") for t in (3, 9, 15, 21, 27, 33, 39, 45, 51)]
    assert disclosure_card(late, {}, tmp_path).at == 54.0


def test_timeline_maps_sections_past_the_sting(tmp_path):
    script = _script()
    srt = _srt(tmp_path, script)
    marks = packaging.section_marks(script, srt, 130)
    assert marks[0] == ("الافتتاحية", 0.0) and abs(marks[1][1] - 24 * 0.4) < 0.01
    assert packaging.to_final(5.0, (9.0, 4.0)) == 5.0 and packaging.to_final(9.6, (9.0, 4.0)) == 13.6
    tl = json.loads(packaging.write_timeline(tmp_path, script, srt, CFG, (9.0, 4.0), 15.0, 200.0).read_text(encoding="utf-8"))
    assert tl["sections"][1]["start"] == round(9.6 + 4.0, 2) and tl["end_card"] == {"start": 185.0, "seconds": 15.0}
    sections, dur = desc.load_sections(tmp_path, CFG)
    assert dur == 200.0 and sections[0] == ("الافتتاحية", 0.0)


def test_english_week_uploads_with_english_title_and_language():
    from datetime import datetime, timezone
    from pipeline.publish import youtube_upload as yu
    cfg = {"publish": {"tags": [], "privacy": "unlisted"}}
    plan = {"episode_title_ar": "عنوان", "episode_title_en": "AI Week: the deal", "language": "en"}
    body = yu.video_body(plan, "d", cfg, datetime(2026, 11, 8, tzinfo=timezone.utc), {"en": {"title": "x"}})
    assert body["snippet"]["title"] == "AI Week: the deal" and body["snippet"]["defaultLanguage"] == "en"
    assert "localizations" not in body


def test_guide_cards_put_topics_and_pivot_questions_on_screen(tmp_path):
    """First viewers, 2026-11-12: show the topic and the question in text when the talk moves on."""
    from pipeline.post import overlays
    script = ("[Section: Opening]\n\nHello there everyone.\n\n[Pause]\n\n[Section: ADNOC and G42]\n\n"
              "They signed a deal this week. Why does this matter for us here?\n\n[Pause]\n\nBecause it does. "
              "Is it big? Yes it is.\n\n[Section: Wrap-up]\n\nThat is all for this week, thanks.\n")
    cards = overlays.guide_cards(script, 150, tmp_path, None, 60.0, {})
    topics = [c for c in cards if c.cue.kind == "topic"]
    assert [c.cue.text for c in topics] == ["ADNOC and G42", "Wrap-up"]          # the cold open has no chip
    assert topics[0].at + topics[0].seconds < topics[1].at and topics[1].at + topics[1].seconds <= 60
    assert [c.cue.text for c in cards if c.cue.kind == "question"] == ["Why does this matter for us here?"]
    assert overlays.guide_cards(script, 150, tmp_path, None, 60.0, {"topics": False, "questions": False}) == []
