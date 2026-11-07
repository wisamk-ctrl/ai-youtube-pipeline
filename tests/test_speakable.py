from pipeline.post.visuals import plan
from pipeline.script_format import speakable, to_tts_text

PRON = {"G42": "جي فورتي تو", "Claude": "كلود", "Claude Code": "كلود كود"}


def test_name_written_twice_is_said_once():
    for text, kept in [("من أوبن إيه آي OpenAI اليوم", "من أوبن إيه آي اليوم"),
                       ("بيربلكسيتي Perplexity", "بيربلكسيتي"),
                       ("بالإمارات، وأدنوك ADNOC.", "بالإمارات، وأدنوك."),
                       ("تينسنت Tencent", "تينسنت"),
                       ("موجود على أوبن راوتر OpenRouter.", "موجود على أوبن راوتر.")]:
        assert speakable(text, {}) == kept


def test_english_that_is_not_a_repeat_stays():
    for text in ["أعلنت عن GPT-6 Cyber.", "أمازون AWS", "حسب مجلة AI Magazine", "على GitHub"]:
        assert speakable(text, {}) == text


def test_bracketed_english_gloss_is_dropped():
    assert speakable("عند الوكلاء الأذكياء (AI agents) اليوم", {}) == "عند الوكلاء الأذكياء اليوم"
    assert speakable("المعالج (وهو مهم) هون", {}) == "المعالج (وهو مهم) هون"


def test_pronunciation_map_and_vowel_marks():
    assert speakable("مجموعة G42 ونزّلت Claude Code و Claude", PRON) == "مجموعة جي فورتي تو ونزّلت كلود كود و كلود"
    assert speakable("عن بُعد", {}) == "عن بعد"          # harakat go, shadda (نزّلت above) stays


def test_tts_text_applies_voice_fixes_by_default():
    assert "OpenAI" not in to_tts_text("أوبن إيه آي OpenAI [Pause]", "ellipsis")
    assert "OpenAI" in to_tts_text("أوبن إيه آي OpenAI", "ellipsis", voice_fixes=False)


def test_corner_off_renders_corner_shots_full_screen():
    script = "[Face] كلام " * 3 + "[Corner: stock robot] " + "كلمة " * 60
    modes_on = {s.mode for s in plan(script, 60.0, corner=True)}
    modes_off = {s.mode for s in plan(script, 60.0, corner=False)}
    assert "corner" in modes_on and "corner" not in modes_off
