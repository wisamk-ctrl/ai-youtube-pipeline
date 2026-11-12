"""Voice-first route: voice pack, voice.yaml, assemble, and face-only shot plan."""

import json
import shutil
import subprocess

import pytest

from pipeline.config import load_settings
from pipeline.post.visuals import plan
from pipeline.video import voicefirst

SENT = "هاي جملة فيها خمس كلمات."          # 5 words


def directed(n_mid: int = 40) -> str:
    return ("[Face]\n" + " ".join([SENT] * 6) + "\n[Pause]\n" + SENT
            + "\n[Visual: stock robot]\n" + " ".join([SENT] * n_mid)
            + "\n[Face]\nكلام بالنص.\n[Corner: stock chip]\n" + " ".join([SENT] * n_mid)
            + "\n[Face]\n" + " ".join([SENT] * 6) + " مع السلامة.")


def test_pack_face_first_and_last_capped_on_sentences():
    cfg = load_settings()
    chunks = voicefirst.pack(directed(), cfg)
    assert chunks[0]["role"] == "face" and chunks[-1]["role"] == "face"
    assert [c["role"] for c in chunks].count("face") == 2          # the middle [Face] is voice
    cap = cfg["visuals"]["face_keep_seconds"] * cfg["scripting"]["words_per_minute"] / 60
    for c in (chunks[0], chunks[-1]):
        assert voicefirst._words(c["text"]) <= cap and c["text"].rstrip().endswith(".")
    assert chunks[0]["text"].startswith("هاي") and chunks[-1]["text"].endswith("مع السلامة.")
    # Every spoken word is in exactly one chunk, in order.
    joined = " ".join(c["text"] for c in chunks)
    assert voicefirst._words(joined) == 6 * 5 + 5 + 80 * 5 + 2 + 6 * 5 + 2
    assert [c["id"] for c in chunks] == [f"{n:02d}-{c['role']}" for n, c in enumerate(chunks, 1)]


def test_pack_voice_chunks_fit_the_limit_and_keep_breaks():
    cfg = load_settings()
    cfg["video"]["voicefirst"]["max_chars"] = 600
    chunks = voicefirst.pack(directed(200), cfg)
    voice = [c for c in chunks if c["role"] == "voice"]
    assert len(voice) > 2 and all(len(c["text"]) <= 600 for c in voice)
    assert any('<break time="0.8s"/>' in c["text"] for c in chunks)
    assert not any("[" in c["text"] for c in chunks)


def test_undirected_script_has_no_pack(tmp_path):
    assert voicefirst.pack("كلام بدون علامات.", load_settings()) == []
    assert voicefirst.write_voice_pack("كلام بدون علامات.", load_settings(), tmp_path) is None


def test_voice_yaml_must_match_the_pack(tmp_path):
    chunks = [{"id": "01-face", "role": "face", "text": "a"}, {"id": "02-voice", "role": "voice", "text": "b"}]
    p = tmp_path / "voice.yaml"
    p.write_text("01-face: {audio: https://r/a.mp3, video: https://f/a.mp4, duration: 2.5}\n02-voice: https://r/b.mp3\n")
    got = voicefirst.load_voice(p, chunks)
    assert [e["id"] for e in got] == ["01-face", "02-voice"] and got[0]["duration"] == 2.5 and got[1]["video"] == ""
    p.write_text("01-face: {audio: https://r/a.mp3, video: https://f/a.mp4}\n03-voice: https://r/b.mp3\n")
    with pytest.raises(ValueError, match="does not match"):
        voicefirst.load_voice(p, chunks)
    p.write_text("01-face: https://r/a.mp3\n02-voice: https://r/b.mp3\n")
    got = voicefirst.load_voice(p, chunks)          # no face video: the chunk is narration only
    assert (got[0]["id"], got[0]["role"], got[0]["video"]) == ("01-face", "voice", "")
    p.write_text("01-face: {audio: https://r/a.mp3, video: face.mp4}\n02-voice: https://r/b.mp3\n")
    with pytest.raises(ValueError, match="video"):
        voicefirst.load_voice(p, chunks)


def test_face_only_spans_are_the_only_faces():
    script = directed()
    shots = plan(script, 120.0, corner=False, face_mode="minimal", face_keep=8.0, face_only=[(0.0, 7.0), (110.0, 118.0)])
    faces = [(s.start, s.end) for s in shots if s.mode == "face"]
    assert faces == [(0.0, 7.0), (110.0, 118.0)]
    assert shots[0].start == 0.0 and shots[-1].end == 120.0
    assert all(abs(a.end - b.start) < 1e-6 for a, b in zip(shots, shots[1:]))


def _media(path, src: str, seconds: float, video: bool = False):
    args = ["ffmpeg", "-y", "-loglevel", "error"]
    if video:
        args += ["-f", "lavfi", "-i", f"testsrc=size=320x180:rate=30:duration={seconds}"]
    args += ["-f", "lavfi", "-i", f"{src}:duration={seconds}"]
    args += (["-shortest", "-c:v", "libx264", "-c:a", "aac"] if video else []) + [str(path)]
    subprocess.run(args, check=True)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_assemble_places_faces_on_the_narration(tmp_path, monkeypatch):
    media = tmp_path / "media"
    media.mkdir()
    _media(media / "a.wav", "sine=frequency=300", 2.0)
    _media(media / "b.wav", "sine=frequency=500", 3.0)
    _media(media / "c.wav", "sine=frequency=700", 1.5)
    _media(media / "fa.mp4", "sine=frequency=300", 2.0, video=True)
    _media(media / "fc.mp4", "sine=frequency=700", 1.5, video=True)
    files = {"https://r/a": "a.wav", "https://r/b": "b.wav", "https://r/c": "c.wav",
             "https://f/a": "fa.mp4", "https://f/c": "fc.mp4"}

    def fake_download(url, dest):
        shutil.copy(media / files[url], dest)
        return dest
    monkeypatch.setattr(voicefirst, "download", fake_download)
    cfg = load_settings()
    cfg["visuals"].update(width=320, height=180)
    out = tmp_path / "week"
    out.mkdir()
    entries = [{"id": "01-face", "role": "face", "audio": "https://r/a", "video": "https://f/a", "duration": None},
               {"id": "02-voice", "role": "voice", "audio": "https://r/b", "video": "", "duration": None},
               {"id": "03-face", "role": "face", "audio": "https://r/c", "video": "https://f/c", "duration": None}]
    dest = voicefirst.assemble(entries, cfg, out)
    gap = cfg["video"]["voicefirst"]["gap_seconds"]
    total = 2.0 + 3.0 + 1.5 + 2 * gap
    assert abs(voicefirst._duration(out / "narration.wav") - total) < 0.05
    assert abs(voicefirst._duration(dest) - total) < 0.1
    streams = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(dest)],
                             capture_output=True, text=True).stdout.split()
    assert "video" in streams and "audio" in streams
    spans = json.loads((out / "face_spans.json").read_text())
    assert [s["id"] for s in spans] == ["01-face", "03-face"]
    assert spans[0]["start"] == 0.0 and abs(spans[0]["end"] - 2.0) < 0.02
    assert abs(spans[1]["start"] - (5.0 + 2 * gap)) < 0.02
    assert voicefirst.face_spans(out) == [(s["start"], s["end"]) for s in spans]

    def mean_luma(t):   # testsrc is bright; the backdrop is dark
        raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(t), "-i", str(dest), "-frames:v", "1",
                              "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
        return sum(raw) / len(raw)
    assert mean_luma(1.0) > 60 and mean_luma(3.5) < 30 and mean_luma(spans[1]["start"] + 0.7) > 60
    (out / "talking_head.source.txt").write_text("manual import\n")
    assert voicefirst.face_spans(out) is None


def test_own_voice_narration_with_optional_selfies(tmp_path, monkeypatch):
    from pipeline.video import manual, voicefirst
    monkeypatch.setattr(manual, "resolve", lambda ref, api_key=None: ref.replace("share", "direct"))
    p = tmp_path / "voice.yaml"
    p.write_text("narration: https://x/share/read.m4a\nclose: https://x/share/bye.mp4\n", encoding="utf-8")
    e = voicefirst.load_voice(p, [])
    assert [x["id"] for x in e] == ["narration", "close"]
    assert e[0]["role"] == "voice" and e[1]["role"] == "face" and e[1]["video"] == "https://x/direct/bye.mp4"
    p.write_text("open: https://x/a.mp4\n", encoding="utf-8")
    import pytest
    with pytest.raises(ValueError):
        voicefirst.load_voice(p, [])
