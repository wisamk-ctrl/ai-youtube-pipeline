"""Visual standard: director pass, shot timeline, assets and the editor."""

import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from pipeline.models import NewsItem
from pipeline.post import visual_assets, visuals
from pipeline.script_format import extract_shots, spoken_text
from pipeline.scripting import director

SCRIPT = """[Section: الافتتاحية]
[Show B-Roll: server racks in a data centre]
شركة إماراتية بتدرس تبني مصنع ذكاء اصطناعي بأوروبا.
[On-Screen Text: 80%]
وتمانين بالمية من الأسئلة بتنحل بدون مهندس.
ليش هاد بيهمّنا؟
[Pause]
لأنه الشركات عنّا ممكن تستفيد.
والقصة لسّا بأولها، وبنتابعها الأسبوع الجاي."""

ITEM = NewsItem(source="ET Datacenters", source_type="rss", title="G42 to explore AI factory in Greece",
                summary="", url="https://x.com/a", published=datetime(2026, 10, 22, tzinfo=timezone.utc))


# ── director ────────────────────────────────────────────────────────────────
def test_auto_direct_keeps_every_word_and_follows_the_shape():
    out = director.auto_direct(SCRIPT)
    assert spoken_text(out).split() == spoken_text(SCRIPT).split()
    shots = extract_shots(out)
    assert shots[0].mode == "face"
    assert any(s.kind == "stock" and "server racks" in s.payload for s in shots)
    assert any(s.kind == "number" and s.payload.startswith("80%") for s in shots)
    assert "[Show B-Roll" not in out
    assert director.check(SCRIPT, out, []) == []
    lines = out.splitlines()
    answer = lines.index("لأنه الشركات عنّا ممكن تستفيد.")
    assert not lines[answer - 1].startswith("[Visual")   # the «ليش بيهمّنا» answer stays on the face


def test_check_refuses_changed_words_and_unknown_sources():
    changed = SCRIPT.replace("بتدرس", "بتفكّر") + "\n[Face]"
    assert any("spoken words changed" in p for p in director.check(SCRIPT, changed, [ITEM]))
    bad = "[Visual: source nope]\n" + SCRIPT
    assert any("unknown source ids" in p for p in director.check(SCRIPT, bad, [ITEM]))


class FakeClient:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = 0
        self.messages = SimpleNamespace(parse=self._parse)

    def _parse(self, **kw):
        self.calls += 1
        out = director.Directed(script=self.outputs.pop(0))
        return SimpleNamespace(stop_reason="end_turn", parsed_output=out, usage=None)


def test_direct_accepts_a_clean_answer():
    good = f"[Face]\n{SCRIPT.replace('[Show B-Roll: server racks in a data centre]', f'[Visual: source {ITEM.id}]')}"
    cfg = {"scripting": {"model": "m"}, "visuals": {}}
    assert director.direct(SCRIPT, [ITEM], cfg, FakeClient([good])) == good.strip()


def test_direct_falls_back_when_the_model_keeps_rewriting():
    bad = "[Face]\n" + SCRIPT.replace("بتدرس", "بتفكّر")
    client = FakeClient([bad, bad])
    out = director.direct(SCRIPT, [ITEM], {"scripting": {"model": "m"}, "visuals": {}}, client)
    assert client.calls == 2
    assert spoken_text(out).split() == spoken_text(SCRIPT).split()
    assert extract_shots(out)


# ── timeline ────────────────────────────────────────────────────────────────
def _srt(tmp_path: Path, cues: list[tuple[float, float, str]]) -> Path:
    def ts(x):
        return f"00:00:{int(x):02d},{int(round((x % 1) * 1000)):03d}"
    p = tmp_path / "s.srt"
    p.write_text("\n\n".join(f"{i}\n{ts(a)} --> {ts(b)}\n{t}" for i, (a, b, t) in enumerate(cues, 1)), encoding="utf-8")
    return p


def test_plan_snaps_cuts_to_sentence_starts(tmp_path):
    script = "[Face]\nواحد اتنين تلاتة أربعة.\n[Visual: title عنوان]\nخمسة ستة سبعة تمانية."
    srt = _srt(tmp_path, [(0.0, 3.8, "واحد اتنين تلاتة أربعة"), (4.2, 8.0, "خمسة ستة سبعة تمانية")])
    shots = visuals.plan(script, 8.0, srt)
    assert [(s.mode, s.start, s.end) for s in shots] == [("face", 0.0, 4.2), ("visual", 4.2, 8.0)]


def test_long_visual_switches_to_corner_halfway():
    script = "[Face]\nكلمة.\n[Visual: title عنوان]\n" + " ".join(["كلمة"] * 60)
    shots = visuals.plan(script, 30.0, None, max_visual=12)
    assert [s.mode for s in shots][-2:] == ["visual", "corner"]


def test_lint_flags_too_much_face():
    shots = [visuals.Shot("face", "", "", 0, 25), visuals.Shot("visual", "title", "x", 25, 30)]
    report = visuals.lint(shots, {})
    assert report["face_share"] > 0.8
    assert any("face on screen" in w for w in report["warnings"])
    assert any("face stretch" in w for w in report["warnings"])
    assert "Against the visual standard" in visuals.shotlist_md(shots, report, estimated=False)


# ── assets ──────────────────────────────────────────────────────────────────
def test_figures_count_up_in_their_own_format():
    for fig, half in [("80%", "40%"), ("$1.25T", "$0.62T"), ("960,000 GPU", "480,000 GPU"), ("٣٧٪", "18٪")]:
        parts = visual_assets.split_figure(fig)
        assert visual_assets.fmt_figure(parts, parts[1] * 0.5) == half
    assert visual_assets.split_figure("بدون رقم") is None


def test_pick_file_prefers_the_smallest_landscape_file_that_fills_the_frame():
    video = {"video_files": [
        {"file_type": "video/mp4", "width": 1280, "height": 720, "link": "a"},
        {"file_type": "video/mp4", "width": 3840, "height": 2160, "link": "b"},
        {"file_type": "video/mp4", "width": 1920, "height": 1080, "link": "c"},
        {"file_type": "video/mp4", "width": 1080, "height": 1920, "link": "portrait"}]}
    assert visual_assets.pick_file(video, 1920)["link"] == "c"
    assert visual_assets.pick_file(video, 5000)["link"] == "b"


def test_fetch_stock_skips_used_clips_and_records_credit(tmp_path, monkeypatch):
    vids = [{"id": 1, "duration": 20, "width": 1920, "url": "u1", "user": {"name": "A", "url": "ua"},
             "video_files": [{"file_type": "video/mp4", "width": 1920, "height": 1080, "link": "l1"}]},
            {"id": 2, "duration": 20, "width": 1920, "url": "u2", "user": {"name": "B", "url": "ub"},
             "video_files": [{"file_type": "video/mp4", "width": 1920, "height": 1080, "link": "l2"}]}]
    monkeypatch.setattr(visual_assets, "pexels_search", lambda q, k, per_page=8: vids)
    import pipeline.video.common as common
    monkeypatch.setattr(common, "download", lambda url, dest: dest.write_bytes(b"x") or dest)
    used = {1}
    path, credit = visual_assets.fetch_stock("chips", tmp_path, used, "key", 1920, 5)
    assert credit["pexels_id"] == 2 and credit["author"] == "B" and path.name == "pexels_2.mp4"
    assert used == {1, 2}


def test_stock_without_a_key_falls_back_to_the_face(tmp_path, monkeypatch):
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)
    shots = [visuals.Shot("face", "", "", 0, 2), visuals.Shot("visual", "stock", "chips", 2, 6)]
    clips, credits = visual_assets.build(shots, [], {"visuals": {}}, tmp_path)
    assert clips == {} and credits == []
    assert "no PEXELS_API_KEY" in shots[1].notes[0]


# ── editor (needs ffmpeg and Chromium) ───────────────────────────────────────
def _chromium_ok() -> bool:
    try:
        with visual_assets.Renderer(64, 36):
            return True
    except Exception:
        return False


@pytest.mark.skipif(not shutil.which("ffmpeg") or not _chromium_ok(), reason="needs ffmpeg and Chromium")
def test_compose_cuts_face_visuals_and_corner_over_the_original_audio(tmp_path):
    from pipeline.post import edit
    th = tmp_path / "th.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=640x360:r=25:d=8",
                    "-f", "lavfi", "-i", "sine=d=8", "-shortest", "-pix_fmt", "yuv420p", str(th)], check=True)
    cfg = {"visuals": {"width": 320, "height": 180, "fps": 25}}
    shots = [visuals.Shot("face", "", "", 0, 2), visuals.Shot("visual", "source", ITEM.id, 2, 4),
             visuals.Shot("visual", "number", "80% | تجربة", 4, 6), visuals.Shot("corner", "title", "عنوان", 6, 8)]
    clips, _ = visual_assets.build(shots, [ITEM], cfg, tmp_path)
    assert set(clips) == {1, 2, 3}
    out = edit.compose(th, shots, clips, cfg, tmp_path)
    assert abs(edit.duration(out) - 8.0) < 0.15
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height",
                            "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout
    assert "video,320,180" in probe and "audio" in probe
