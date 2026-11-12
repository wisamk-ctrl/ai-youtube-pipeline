"""The script-guided own-voice edit (pipeline/video/guided.py): the script decides what stays."""

import shutil
import subprocess
import wave

import numpy as np
import pytest

from pipeline.post.subtitles import Word
from pipeline.video import guided

SCRIPT = ("خلّينا نبلّش من الخليج. حسب رويترز، أدنوك ومجموعة جي فورتي تو وقّعوا صفقة مع أوبن. "
          "الوكلاء. الوكلاء بلّشوا يطلعوا من لابتوب المطوّر، ويصيروا بنية تحتية إلها قواعد وحوكمة. "
          "أمازون نشرت كيف تشغّل كلود كود على منصة Bedrock AgentCore. كل مهمة بتشتغل بجلسة معزولة.")


def say(text: str, t: float = 0.0, step: float = 0.4, gaps: dict[int, float] | None = None) -> list[Word]:
    out = []
    for n, w in enumerate(text.split()):
        t += (gaps or {}).get(n, 0.0)
        out.append(Word(round(t, 3), round(t + step - 0.05, 3), w))
        t += step
    return out


def run(heard: list[Word], files: list[int] | None = None, **kw):
    files = files or [0] * len(heard)
    lengths = [max(w.end for w, f in zip(heard, files) if f == n) + 1 for n in sorted(set(files))]
    plan, spans, at, raw = guided.guide(SCRIPT, heard, files, lengths, **kw)
    kept = [heard[k].word for a, b in plan.pieces for k in range(a, b + 1)]
    return plan, spans, kept


def cut_text(plan, heard) -> list[str]:
    return [" ".join(w.word for w in heard[a:b + 1]) for a, b, _ in plan.dropped]


def test_a_clean_read_is_kept_whole():
    heard = say(SCRIPT)
    plan, spans, kept = run(heard)
    assert kept == SCRIPT.split() and not plan.dropped and not plan.unheard and len(plan.pieces) == 1


def test_the_scripts_own_repeat_is_not_a_stumble():
    plan, _, kept = run(say(SCRIPT))
    assert kept.count("الوكلاء.") + kept.count("الوكلاء") == 2


def test_a_retake_keeps_the_later_saying():
    heard = say("خلينا نبلش من الخليج حسب رويترز ادنوك ومجموعة جي فورتي تو وقعوا صفقة مع اوبن الوكلاء الوكلاء "
                "بلشوا يطلعوا من لابتوب المطور يطلعوا من لابتوب المطور ويصيروا بنية تحتية الها قواعد وحوكمة "
                "امازون نشرت كيف تشغل كلود كود على منصة Bedrock AgentCore كل مهمة بتشتغل بجلسة معزولة")
    plan, _, kept = run(heard)
    assert cut_text(plan, heard) == ["يطلعوا من لابتوب المطور"] and plan.dropped[0][2] == "retake"
    assert plan.dropped[0][0] == 18                      # the first saying goes, the second stays
    assert len(kept) == len(SCRIPT.split())


def test_a_doubled_word_and_a_respoken_name_are_cut():
    heard = say("خلينا نبلش من الخليج حسب رويترز ادنوك ومجموعة ومجموعة جي فورتي تو وقعوا صفقة مع اوبن الوكلاء "
                "الوكلاء بلشوا يطلعوا من لابتوب المطور ويصيروا بنية تحتية الها قواعد وحوكمة امازون نشرت كيف تشغل "
                "كلود كود على منصة Bedrock Agent Core أو Agent Core Bedrock كل مهمة بتشتغل بجلسة معزولة")
    plan, _, kept = run(heard)
    assert cut_text(plan, heard) == ["ومجموعة", "أو Agent Core Bedrock"]
    assert "Agent" in kept and kept.count("Bedrock") == 1          # «Agent Core» is the script's «AgentCore»


def test_an_ad_lib_stays():
    heard = say(SCRIPT.replace("حسب رويترز،", "طيب يعني حسب رويترز،"))
    plan, _, kept = run(heard)
    assert not plan.dropped and "طيب" in kept


def test_a_pickup_file_replaces_the_sentence_in_place():
    main = say(SCRIPT.replace("جي فورتي تو وقّعوا صفقة", "جي تو فورتي وقّعوا صفقات"))
    pick = say("حسب رويترز، أدنوك ومجموعة جي فورتي تو وقّعوا صفقة مع أوبن.")
    heard = main + pick
    files = [0] * len(main) + [1] * len(pick)
    plan, spans, kept = run(heard, files)
    assert " ".join(kept) == SCRIPT                      # script order, the pickup's words in the middle
    assert [s.file for s in spans] == [0, 1, 0]
    assert "صفقات" in " ".join(cut_text(plan, heard))


def test_given_spans_force_and_forbid_cuts():
    heard = say(SCRIPT.replace("ومجموعة", "ومجموعة ومجموعة"))
    first = next(k for k, w in enumerate(heard) if w.word == "ومجموعة")
    span = [(heard[first].start, heard[first + 1].end)]
    plan, _, kept = run(heard, keep=span)
    assert kept.count("ومجموعة") == 2 and not plan.dropped
    plan, _, kept = run(heard, cut=[(heard[0].start, heard[1].end)])
    assert kept[0] == "من" and ("given" in [d[2] for d in plan.dropped])


def test_a_passage_never_said_is_listed():
    heard = say(SCRIPT.replace("ويصيروا بنية تحتية إلها قواعد وحوكمة.", ""))
    plan, _, _ = run(heard)
    raw, _ = guided.script_tokens(SCRIPT)
    assert [" ".join(raw[a:b + 1]) for a, b in plan.unheard] == ["ويصيروا بنية تحتية إلها قواعد وحوكمة."]


def test_long_pauses_are_capped_and_words_move_with_the_audio(tmp_path):
    heard = say(SCRIPT, t=1.0, gaps={5: 3.0})
    plan, spans, _ = run(heard)
    assert len(spans) == 2
    rate, total = 48000, heard[-1].end + 1
    wav = tmp_path / "in.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(2), w.setsampwidth(2), w.setframerate(rate)
        w.writeframes((np.ones((int(total * rate), 2)) * 1000).astype("<i2").tobytes())
    moved = guided.render([wav], spans, tmp_path / "out.wav", heard)
    data, _ = guided.read_wav(tmp_path / "out.wav")
    assert len(moved) == len(heard)
    assert abs(len(data) / rate - (total - 1.0 - 2.5 - 0.7 + 0.08 + 0.3)) < 0.2     # 3.4 s pause → 0.5 s
    gap = moved[5].start - moved[4].end
    assert 0.5 <= gap <= 0.75
    assert abs(data[: int(0.001 * rate)]).max() < 200                                # faded in


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
def test_clean_guided_end_to_end(tmp_path, monkeypatch):
    from pipeline.video import ownvoice
    heard = say("خلينا نبلش من من الخليج", t=0.5)
    src = tmp_path / "read.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=220:duration=4",
                    str(src)], check=True)
    seen = {}

    def fake(path, model=None, cache=True, language=None, vad=True, key=None):
        seen.update(model=model, vad=vad, key=key)
        return heard
    monkeypatch.setattr(ownvoice, "transcribe_words", fake)
    dest, report, moved = ownvoice.clean_guided([src], tmp_path / "clean.wav", "خلّينا نبلّش من الخليج.", {})
    assert dest.exists() and [w.word for w in moved] == ["خلينا", "نبلش", "من", "الخليج"]
    assert seen["model"] == "large-v3-turbo" and seen["vad"] is False and seen["key"].endswith(":novad")
    assert "1 retake(s)" in report or "1 stumble(s)" in report


def test_voice_yaml_takes_several_files_and_pickups():
    from pipeline.video.voicefirst import own_voice
    e = own_voice({"narration": ["https://x/a.m4a", "https://x/b.m4a"], "pickups": ["https://x/p.m4a"],
                   "keep": ["1:00-1:02"]})[0]
    assert e["audio"] == "https://x/a.m4a" and e["more"] == ["https://x/b.m4a", "https://x/p.m4a"]
    assert e["guided"] is True and e["keep"] == ["1:00-1:02"]
    assert own_voice({"narration": "https://x/a.m4a", "guided": False})[0]["guided"] is False


def test_a_name_in_either_alphabet_is_the_same_name():
    assert guided.skeleton("اوكتا") == guided.skeleton("okta") and guided.skeleton("بدروك") == guided.skeleton("bedrock")
    assert guided._sim("كلاود", "cloud") and guided._sim("فرتكس", "vertex") and guided._sim("سايبر", "cyber")
    assert not guided._sim("كتاب", "cloud")
    heard = say("خلينا نبلش من الخليج حسب رويترز ادنوك ومجموعة جي فورتي تو وقعوا صفقة مع اوبن الوكلاء الوكلاء "
                "بلشوا يطلعوا من لابتوب المطور ويصيروا بنية تحتية الها قواعد وحوكمة امازون نشرت كيف تشغل كلود كود "
                "على منصة بدروك اي جنت كور او اي جنت كور بدروك كل مهمة بتشتغل بجلسة معزولة")
    plan, _, kept = run(heard)
    assert cut_text(plan, heard)[-1].endswith("جنت كور بدروك") and kept.count("بدروك") == 1
    assert not plan.unheard


def test_tiny_words_are_never_cut_as_repeats():
    script = "بتنحفظ أو لا. والمنصة داخلة بنطاق شهادات زي SOC وISO، وبتنفع تستخدمها"
    heard = say("بتنحفظ او لا والمنصة داخلة بنطاق شهادات زي اس سوك او ايزو وبتنفع تستخدمها")
    plan, _, at, raw = guided.guide(script, heard, [0] * len(heard), [heard[-1].end + 1])
    assert not plan.dropped


def test_the_reading_script_is_the_text_under_its_headings():
    md = "# W45 — نص القراءة\n\n~1106 كلمة · حوالي 9 دقائق\n\n## الافتتاحية (سيلفي)\n\nأهلا فيكم.\n\n## النص\n\nخلّينا نبلّش."
    assert guided.reading_text(md) == "أهلا فيكم.\n\n\nخلّينا نبلّش."


def test_a_word_said_out_of_order_is_kept():
    script = "وناوية تستخدم Vera بنظام إنتاج جاي. ودايتونا شغّلت ألف بيئة"
    heard = say("وناوية تستخدم بنظام فيرا بالانتاج الجاي ودايتونا شغلت الف بيئة")
    plan, _, at, raw = guided.guide(script, heard, [0] * len(heard), [heard[-1].end + 1])
    assert not plan.dropped                                   # a misread to check by ear, not a stumble to cut


def test_a_phrase_that_comes_again_later_is_not_a_far_jump():
    script = ("سام ألتمان بالإمارات، وأدنوك وجي فورتي تو بيوقّعوا صفقة ذكاء اصطناعي معها. وبنفس الأسبوع، في موديل جديد. "
              "خلّينا نبلّش من الخليج. حسب رويترز، أدنوك ومجموعة جي فورتي تو وقّعوا صفقة مع الشركة.")
    heard = say("سام التمان بالامارات هو ادنكو جي فورتي تو بوقع صدق ذكاء اصطناعي معه وبنفس الاسبوع في موديل جديد "
                "خلينا نبلش من الخليج حسب رويترز ادنوك ومجموعة جي فورتي تو وقعوا صفقة مع الشركة")
    plan, _, at, raw = guided.guide(script, heard, [0] * len(heard), [heard[-1].end + 1])
    assert not plan.dropped and len(plan.pieces) == 1
