import shutil
import subprocess

import pytest

from pipeline.post import repair
from pipeline.post.subtitles import Word
from pipeline.post.visuals import plan

PRON = {"G42": "جي فورتي تو"}


def heard_for(words, drop=()):
    """One heard word per script word, 0.5 s each; `drop` indexes are merged away like Whisper does."""
    out, t = [], 0.0
    for i, w in enumerate(words):
        if i in drop:
            t += 0.5
            continue
        out.append(Word(t, t + 0.4, w))
        t += 0.5
    return out


def test_doubled_name_is_widened_to_clean_anchors():
    script = "وقّعت من أوبن إيه آي OpenAI صفقة كبيرة اليوم"
    words = script.split()
    repairs, skipped = repair.find(script, heard_for(words, drop={5}), pron={})
    assert not skipped and len(repairs) == 1
    r = repairs[0]
    assert r.phrase == "أوبن إيه آي OpenAI" and r.say == "أوبن إيه آي"
    assert (r.start, r.end) == (1.0, 3.0)          # from «أوبن» to the start of «صفقة»


def test_mispronounced_name_and_hand_listed_phrase():
    script = "مجموعة وG42 بتشتغل عن بُعد على المنصة"
    repairs, _ = repair.find(script, heard_for(script.split()), pron=PRON, fixes=["عن بُعد"])
    says = [r.say for r in repairs]
    assert "وجي فورتي تو" in says and "عن بعد" in says


def test_gloss_not_spoken_is_left_alone():
    script = "عند الوكلاء (AI agents) اليوم الصبح"
    words = script.split()
    repairs, skipped = repair.find(script, heard_for(words, drop={2, 3}), pron={})
    assert not repairs and "not spoken" in skipped[0]


def test_retime_drops_replaced_words_and_shifts_later_ones():
    heard = [Word(0, 0.4, "a"), Word(1.0, 1.4, "b"), Word(3.0, 3.4, "c")]
    out = repair.retime(heard, [(0.9, 2.0, 0.0, -0.5)])
    assert [(w.word, w.start) for w in out] == [("a", 0), ("c", 2.5)]


def test_hidden_spans_and_minimal_face():
    script = "[Face] " + "كلمة " * 20 + "[Visual: stock robot] " + "كلمة " * 20 + "[Face] " + "كلمة " * 20 \
             + "[Visual: stock chip] " + "كلمة " * 20 + "[Face] " + "كلمة " * 20
    shots = plan(script, 100.0, face_mode="minimal", face_keep=8, corner=False)
    faces = [s for s in shots if s.mode == "face"]
    assert len(faces) == 2 and all(s.seconds <= 8 + 1e-6 for s in faces)
    assert faces[0].start == 0 and abs(faces[-1].end - 100) < 1e-6
    hidden = plan(script, 100.0, hide=[(1.0, 2.0)])
    assert hidden[0].mode == "visual"


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_apply_splices_a_clip(tmp_path, monkeypatch):
    video = tmp_path / "v.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=320x240:rate=30:duration=6",
                    "-f", "lavfi", "-i", "sine=frequency=300:duration=6", "-shortest", "-c:v", "libx264",
                    "-c:a", "aac", str(video)], check=True)
    clip = tmp_path / "c.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=600:duration=1",
                    str(clip)], check=True)
    monkeypatch.setattr(repair, "_clip", lambda url, dest: clip)
    r = repair.Repair((1, 2), 2.0, 4.0, "x", "y", "test", audio="https://example.invalid/c.mp3")
    out, hides, heard = repair.apply(video, [r], [Word(0.5, 1.0, "a"), Word(5.0, 5.5, "b")], tmp_path, fps=30)
    length = 1 + 2 * repair.PAD
    assert abs(repair._duration(out) - (6 - 2 + length)) < 0.15
    assert hides == [(2.0, round(2.0 + length, 3))]
    assert heard[-1].start == pytest.approx(5.0 - 2 + length, abs=1e-3)


def test_hide_inside_opening_face_keeps_the_rest_of_the_face():
    script = "[Face] " + "كلمة " * 30 + "[Visual: stock robot] " + "كلمة " * 30
    shots = plan(script, 60.0, hide=[(10.0, 12.0)], corner=False)
    modes = [(s.mode, round(s.start, 1), round(s.end, 1)) for s in shots if s.start < 30]
    assert modes[0][0] == "face" and modes[1][0] == "visual" and modes[2][0] == "face"


def test_clip_keys_ignore_punctuation_and_harakat():
    assert repair.key("أوبن إيه آي، صفقة.") == repair.key("أوبن  إيه آي صفقة")


def test_repair_is_opt_in(tmp_path):
    assert repair.load_voice(tmp_path) is None
    (tmp_path / "repairs.yaml").write_text("fix: [عن بُعد]\nvoice:\n  'أوبن إيه آي.': https://x/y.mp3\n", encoding="utf-8")
    data = repair.load_voice(tmp_path)
    assert data["fix"] == ["عن بُعد"] and data["voice"][repair.key("أوبن إيه آي")] == "https://x/y.mp3"


def test_bad_clip_is_skipped_not_fatal(tmp_path, monkeypatch):
    def boom(url, dest):
        raise OSError("expired")
    monkeypatch.setattr(repair, "_clip", boom)
    r = repair.Repair((0, 1), 1.0, 2.0, "x", "y", "t", audio="https://example.invalid/a.mp3")
    video = tmp_path / "v.mp4"
    out, hides, heard = repair.apply(video, [r], [], tmp_path)
    assert out == video and hides == [] and r.audio == ""


def test_correction_rewrites_script_and_keeps_markers():
    script = "رادار الأسبوع. تينسنت Tencent الصينية لسّا مش [Visual: stock chip] على القائمة. بس هالأسبوع"
    out = repair.apply_corrections(script, {"تينسنت Tencent الصينية لسّا مش على القائمة. بس هالأسبوع": "تينسنت رجعت، وهالأسبوع"})
    assert out == "رادار الأسبوع. تينسنت رجعت، وهالأسبوع [Visual: stock chip]"


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_clip_takes_a_stretch_of_one_recording(tmp_path, monkeypatch):
    src = tmp_path / "all.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=400:duration=5", str(src)],
                   check=True)
    repair._DOWNLOADS[f"https://example.invalid/{tmp_path.name}.mp3"] = src
    out = repair._clip(f"https://example.invalid/{tmp_path.name}.mp3#t=1.0,2.5", tmp_path / "c.wav")
    assert abs(repair._duration(out) - 1.5) < 0.05
