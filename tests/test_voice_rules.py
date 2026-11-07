"""Voice rules: braced names, the Latin allowlist, and the voice lint (review 2026-11-07, Tier 1 #2–#4)."""

from pipeline.post.subtitles import Word, script_captions
from pipeline.script_format import (caption_text, count_spoken_words, extract_shots, lint_voice, speakable,
                                    spoken_words, to_tts_text, voice_lint_md, voice_lint_notes, _voice_config)
from pipeline.scripting.director import check

CFG = {"latin_allowlist": ["AI", "GPU", "CPU", "API"], "banned_phrases": {"عن بعد": "من بعيد", "مقارنة بـ": "إذا قارنّاه بـ"}}


def rules(script, pron=None):
    return [f.rule for f in lint_voice(script, {} if pron is None else pron, CFG)]


def test_braces_are_never_spoken():
    assert speakable("أعلنت أوبن إيه آي{OpenAI} اليوم", {}) == "أعلنت أوبن إيه آي اليوم"
    assert speakable("جوجل ديب مايند{Google DeepMind}، وبعدين", {}) == "جوجل ديب مايند، وبعدين"
    assert "OpenAI" not in to_tts_text("أوبن إيه آي{OpenAI} [Pause] هسّا", "ellipsis")


def test_older_scripts_still_deduped():
    assert speakable("من أوبن إيه آي OpenAI اليوم", {}) == "من أوبن إيه آي اليوم"


def test_braced_name_is_one_word():
    assert spoken_words("من جوجل ديب مايند{Google DeepMind}، اليوم") == ["من", "جوجل", "ديب", "مايند{Google DeepMind}،", "اليوم"]
    assert count_spoken_words("[Section: س]\nأوبن إيه آي{OpenAI} أعلنت") == count_spoken_words("أوبن إيه آي أعلنت") == 4
    shots = extract_shots("أوبن إيه آي{Open AI} أعلنت [Visual: title عنوان] هسّا")
    assert shots[0].at_word == 4


def test_captions_show_the_latin_in_brackets():
    assert caption_text("أوبن إيه آي{OpenAI} أعلنت") == "أوبن إيه آي (OpenAI) أعلنت"
    heard = [Word(i * 0.5, i * 0.5 + 0.4, " " + w) for i, w in enumerate("أوبن إيه آي أعلنت اليوم".split())]
    caps = script_captions("أوبن إيه آي{OpenAI} أعلنت اليوم.", heard)
    assert " ".join(c.text for c in caps) == "أوبن إيه آي (OpenAI) أعلنت اليوم"
    assert abs(caps[0].start - 0.0) < 1e-6


def test_director_check_accepts_braces_and_catches_changes():
    original = "أوبن إيه آي{OpenAI} أعلنت."
    assert not [p for p in check(original, "[Face]\n" + original, []) if p.startswith("spoken")]
    assert [p for p in check(original, "[Face]\nأوبن إيه آي{Open AI} أعلنت.", []) if p.startswith("spoken")]


def test_allowlist_lives_in_config():
    assert set(_voice_config()["latin_allowlist"]) == {"AI", "GPU", "CPU", "API"}


def test_latin_outside_the_allowlist_is_flagged_but_braced_is_not():
    assert rules("الشركة بتستخدم GPU وAPI.") == []
    assert rules("أنثروبيك{Anthropic} نزّلت إشي جديد.") == []
    found = lint_voice("Anthropic نزّلت إشي، وAnthropic كمان.", {}, CFG)
    assert [(f.rule, f.quote, f.detail) for f in found] == [("latin", "Anthropic", "2×")]


def test_mixed_tokens_need_a_respelling():
    assert rules("مجموعة G42 وقّعت.") == ["digits"]
    assert rules("مجموعة G42 وقّعت.", {"G42": "جي فورتي تو"}) == []


def test_version_strings_and_parentheses():
    assert "version" in rules("نزّلوا تحديث 2.1.317 هالأسبوع.")
    assert rules("[On-Screen Text: 2.1.317] نزّلوا آخر إصدار.") == []
    assert rules("المعالج (وهو مهم) هون.") == ["parentheses"]


def test_latin_stack_and_figures_and_preposition_pause():
    assert "latin-stack" in rules("في صلاحيات IAM، واتصال عن طريق PrivateLink، وسجلات بـCloudTrail.")
    assert "figures" in rules("الصفقة خمسين مليار دولار وتلاتين بالمية منها للخليج.")
    assert "figures" not in rules("الصفقة خمسين مليار دولار [Pause] وتلاتين بالمية منها للخليج.")
    assert "figures" not in rules("السرعة عشرة فاصلة تمانية ثانية.")
    assert "preposition-pause" in rules("صفقة لـ [Pause] خمس سنين.")
    assert "preposition-pause" in rules("صفقة لـ ... خمس سنين.")
    assert "preposition-pause" not in rules("صفقة [Pause] لخمس سنين.")


def test_banned_phrases_ignore_harakat_and_match_prefixes():
    found = lint_voice("الشغل عن بُعد صار عادي. مقارنة بالسنة الماضية.", {}, CFG)
    assert sorted(f.quote for f in found if f.rule == "banned") == ["عن بعد", "مقارنة بـ"]


def test_why_it_matters_repeats_and_hook_length():
    script = "ليش بيهمّنا؟ لأنه مهم. ليش هاد بيهمّنا هون؟ لأنه مهم. ليش هاد مهم؟ لأنه جديد."
    assert "why-it-matters" not in rules(script)
    assert "why-it-matters" in rules(script + " ليش بيهمّنا؟ كمان.")
    long_hook = "خبر " * 46 + "أهلاً فيكم بأسبوع الذكاء الاصطناعي."
    assert "hook-length" in rules(long_hook)
    assert "hook-length" not in rules("خبر " * 40 + "أهلاً فيكم.")


def test_report_and_notes():
    found = lint_voice("Anthropic نزّلت تحديث 2.1.317.", {}, CFG)
    md = voice_lint_md(found, "Voice lint · W")
    assert md.startswith("# Voice lint · W") and "## version (1)" in md and "## latin (1)" in md
    notes = voice_lint_notes(found)
    assert "[version] «2.1.317»" in notes and "آخر إصدار" in notes
    assert voice_lint_notes([]) == ""
