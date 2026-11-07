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


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_silence_clip_for_a_dropped_gloss(tmp_path):
    out = repair._clip("silence:0.15", tmp_path / "s.wav")
    assert abs(repair._duration(out) - 0.15) < 0.02


# ── splice quality, on synthetic audio ───────────────────────────────────────
def _tone(path, expr, seconds, video=False):
    """A file whose audio is `expr` (ffmpeg aevalsrc, t in seconds); with a test picture when `video`."""
    args = ["ffmpeg", "-y", "-loglevel", "error"]
    if video:
        args += ["-f", "lavfi", "-i", f"testsrc=size=160x120:rate=30:duration={seconds}"]
    args += ["-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d={seconds}"]
    args += (["-c:v", "libx264", "-c:a", "aac", "-b:a", "192k", "-shortest"] if video else []) + [str(path)]
    subprocess.run(args, check=True)
    return path


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_cut_lands_on_the_quietest_point_between_words(tmp_path):
    # Speech-like tone with a 40 ms hole at 1.13 s; Whisper says word 1 ends at 1.0 and word 2 starts at 1.2.
    wav = _tone(tmp_path / "a.wav", "0.5*sin(2*PI*300*t)*not(between(t,1.13,1.17))", 3)
    env = repair._envelope(wav)
    heard = [Word(0.5, 1.0, "a"), Word(1.2, 1.6, "b")]
    cut = repair.quiet_cut(env, heard, 1.2)
    assert 1.13 <= cut <= 1.17
    assert repair.quiet_cut(env, heard, 2.0) == 2.0          # not a heard word start: left alone


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_room_tone_is_the_quietest_stretch_but_never_digital_silence(tmp_path):
    expr = "if(lt(t,1),0,if(lt(t,2),0.5*sin(2*PI*300*t),if(lt(t,3),0.002*sin(2*PI*1234*t),0.5*sin(2*PI*300*t))))"
    at = repair.room_tone_at(repair._envelope(_tone(tmp_path / "r.wav", expr, 4)))
    assert at is not None and 1.98 <= at <= 2.72
    assert repair.room_tone_at(repair._envelope(_tone(tmp_path / "n.wav", "0.5*sin(2*PI*300*t)", 2))) is None


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_loudness_is_matched_on_speech_not_pauses(tmp_path):
    steady = _tone(tmp_path / "s.wav", "0.3*sin(2*PI*300*t)", 4)
    paused = _tone(tmp_path / "p.wav", "0.3*sin(2*PI*300*t)*lt(mod(t,1),0.5)", 4)   # half the time silent
    assert repair._mean_db(steady) - repair._mean_db(paused) > 2.5                    # the old measure is fooled
    assert abs(repair.speech_db(repair._envelope(steady)) - repair.speech_db(repair._envelope(paused))) < 0.5


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_splice_cuts_in_the_gap_crossfades_and_keeps_length_exact(tmp_path, monkeypatch):
    # Room tone at 0.002 between "words"; holes in the speech at 1.95–2.05 s and 3.95–4.05 s.
    # A longer pause at 5.3–5.9 s is the room tone.
    expr = "if(between(t,1.95,2.05)+between(t,3.95,4.05)+between(t,5.3,5.9),0.002*sin(2*PI*1234*t),0.4*sin(2*PI*300*t))"
    video = _tone(tmp_path / "v.mp4", expr, 6, video=True)
    clip = _tone(tmp_path / "c.wav", "0.1*sin(2*PI*600*t)", 1)
    monkeypatch.setattr(repair, "_clip", lambda url, dest: clip)
    heard = [Word(1.2, 1.9, "a"), Word(2.1, 3.0, "x"), Word(3.1, 3.9, "y"), Word(4.1, 5.0, "b")]
    r = repair.Repair((1, 3), 2.1, 4.1, "x y", "z", "test", audio="https://example.invalid/c.mp3")
    out, hides, retimed = repair.apply(video, [r], heard, tmp_path, fps=30)
    length = 1 + 2 * repair.PAD
    a, b = hides[0][0], hides[0][0] + 4.0 - 2.0             # the cut sits in the first hole, not on 2.1
    assert 1.95 <= a <= 2.05 and hides[0][1] == pytest.approx(a + length, abs=1e-3)
    span = repair.quiet_cut(repair._envelope(video), heard, 4.1) - a
    assert abs(repair._duration(out) - (6 - span + length)) < 0.1
    assert [w.word for w in retimed] == ["a", "b"] and retimed[1].start == pytest.approx(4.1 - span + length, abs=1e-3)
    # The clip (0.1 amplitude) was raised to the render's speech level (0.4): about +12 dB.
    env_out = repair._envelope(out)
    pad = env_out[int((a + 0.02) / repair.HOP):int((a + repair.PAD - 0.02) / repair.HOP)]
    assert 1e-8 < pad.mean() < 1e-4                          # room tone in the padding, not digital silence
    assert abs(repair.speech_db(env_out, a + 0.2, a + 0.9) - repair.speech_db(repair._envelope(video), 0.0, 1.9)) < 1.0
