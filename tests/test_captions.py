"""Captions show the approved script; Whisper only supplies the timing."""

from pipeline.post.subtitles import Word, align, norm_word, script_captions

# What Whisper actually wrote for the Jordanian test clip, one word per 0.5 s.
HEARD_TEXT = "اهلا بكم في اسبوع الذكاء الاصطناعي معكم ويسام قبل اول حلقة خلين انبلش بارقام كبيرة"
SCRIPT = "أهلاً فيكم بـ«أسبوع الذكاء الاصطناعي»، معكم وسام. قبل أول حلقة. خلّينا نبلّش بأرقام كبيرة."


def heard():
    return [Word(i * 0.5, i * 0.5 + 0.4, " " + w) for i, w in enumerate(HEARD_TEXT.split())]


def test_normalisation_unifies_spelling_variants():
    assert norm_word("أهلاً") == norm_word("اهلا")
    assert norm_word("حلقة") == norm_word("حلقه")
    assert norm_word("«أسبوع") == norm_word("اسبوع")


def test_alignment_is_monotonic_and_anchored():
    words = SCRIPT.split()
    times = align(words, heard())
    assert times == sorted(times)
    i = words.index("الذكاء")
    assert abs(times[i] - 2.0) < 1e-6        # «الذكاء» is the 5th heard word, at 2.0 s


def test_captions_use_the_script_wording_not_whisper():
    caps = script_captions(SCRIPT, heard())
    text = " ".join(c.text for c in caps)
    assert "خلّينا نبلّش" in text and "خلين انبلش" not in text
    assert "وسام" in text and "ويسام" not in text
    assert all(c.end > c.start for c in caps)
    assert [c.start for c in caps] == sorted(c.start for c in caps)
    assert caps[-1].end <= heard()[-1].end + 1e-6


def test_no_matches_spreads_the_script_over_the_speech():
    caps = script_captions("كلمة تانية تالتة", [Word(1.0, 1.4, "x"), Word(3.0, 3.4, "y")])
    assert caps[0].start == 1.0 and caps[-1].end <= 3.4


def test_lines_break_at_sentences_and_drop_trailing_commas():
    caps = script_captions(SCRIPT, heard())
    assert all(not c.text.endswith(("،", ".", ":")) for c in caps)
    assert any(c.text.endswith("وسام") for c in caps)          # "معكم وسام." without its full stop
    q = script_captions("بتثقوا بموديل ما درّبتوه بإيدكم؟", heard())
    assert q[-1].text.endswith("؟")
