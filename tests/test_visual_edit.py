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
    assert shots[0].mode == "corner" and shots[0].kind == "stock"   # the story opens in the corner
    assert any(s.kind == "stock" and "server racks" in s.payload for s in shots)
    assert any(s.kind == "number" and s.payload.startswith("80%") for s in shots)
    assert "[Show B-Roll" not in out
    assert director.check(SCRIPT, out, []) == []
    lines = out.splitlines()
    question = lines.index("ليش هاد بيهمّنا؟")
    assert lines[question - 1] == "[Face]"               # a question to the viewer is on the face


def test_check_refuses_changed_words_and_unknown_sources():
    changed = SCRIPT.replace("بتدرس", "بتفكّر") + "\n[Face]"
    assert any("spoken words changed" in p for p in director.check(SCRIPT, changed, [ITEM]))
    bad = "[Visual: source nope]\n" + SCRIPT
    assert any("unknown source ids" in p for p in director.check(SCRIPT, bad, [ITEM]))


class FakeClient:
    """Stands in for client.messages.stream(...) as a context manager."""

    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = 0
        self.messages = SimpleNamespace(stream=self._stream)

    def _stream(self, **kw):
        self.calls += 1
        text = f"<script>\n{self.outputs.pop(0)}\n</script>"
        msg = SimpleNamespace(stop_reason="end_turn", usage=None, content=[SimpleNamespace(text=text)])

        class Ctx:
            def __enter__(self_inner):
                return SimpleNamespace(get_final_message=lambda: msg)

            def __exit__(self_inner, *a):
                return False
        return Ctx()


def test_direct_accepts_a_clean_answer():
    good = f"[Face]\n{SCRIPT.replace('[Show B-Roll: server racks in a data centre]', f'[Visual: source {ITEM.id}]')}"
    cfg = {"scripting": {"model": "m"}, "visuals": {"face_share": [0.0, 1.0]}}   # screen time not under test here
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


def _chromium_ok() -> bool:
    try:
        with visual_assets.Renderer(64, 36):
            return True
    except Exception:
        return False


def test_fetch_stock_skips_used_clips_and_records_credit(tmp_path, monkeypatch):
    vids = [{"id": "pixabay_1", "duration": 20, "width": 1920, "url": "u1", "user": {"name": "A", "url": "ua"},
             "video_files": [{"file_type": "video/mp4", "width": 1920, "height": 1080, "link": "l1"}]},
            {"id": "pixabay_2", "duration": 20, "width": 1920, "url": "u2", "user": {"name": "B", "url": "ub"},
             "video_files": [{"file_type": "video/mp4", "width": 1920, "height": 1080, "link": "l2"}]}]
    import pipeline.video.common as common
    monkeypatch.setattr(common, "download", lambda url, dest: dest.write_bytes(b"x") or dest)
    used = {"pixabay_1"}
    path, credit = visual_assets.fetch_stock("chips", tmp_path, used, lambda q: vids, 1920, 5)
    assert credit["id"] == "pixabay_2" and credit["author"] == "B" and path.name == "pixabay_2.mp4"
    assert used == {"pixabay_1", "pixabay_2"}


def test_pixabay_hits_are_normalised(monkeypatch):
    hit = {"id": 7, "pageURL": "https://pixabay.com/videos/x-7/", "duration": 14, "user": "ann", "user_id": 9,
           "videos": {"large": {"url": "", "width": 0, "height": 0},
                      "medium": {"url": "https://cdn/m.mp4", "width": 1920, "height": 1080},
                      "small": {"url": "https://cdn/s.mp4", "width": 1280, "height": 720}}}
    class R:
        def raise_for_status(self): pass
        def json(self): return {"hits": [hit]}
    seen = {}
    monkeypatch.setattr(visual_assets.requests, "get", lambda url, timeout, params: seen.update(params) or R())
    v = visual_assets.pixabay_search("server racks " * 20, "k")[0]   # animations are asked for first
    assert v["id"] == "pixabay_7" and v["user"]["url"] == "https://pixabay.com/users/ann-9/"
    assert visual_assets.pick_file(v, 1920)["link"] == "https://cdn/m.mp4"   # the empty "large" is ignored
    assert len(seen["q"]) <= 100 and seen["safesearch"] == "true"


def test_stock_provider_order_and_keys(monkeypatch):
    for k in ("PIXABAY_API_KEY", "PEXELS_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    assert visual_assets.stock_search({}) is None
    monkeypatch.setenv("PEXELS_API_KEY", "p")
    assert visual_assets.stock_search({})[0] == "pexels"
    monkeypatch.setenv("PIXABAY_API_KEY", "x")
    assert visual_assets.stock_search({})[0] == "pixabay"


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_stock_without_a_key_becomes_a_branded_backdrop(tmp_path, monkeypatch):
    for k in ("PIXABAY_API_KEY", "PEXELS_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    if not _chromium_ok():
        pytest.skip("needs Chromium")
    shots = [visuals.Shot("face", "", "", 0, 2), visuals.Shot("visual", "stock", "chips", 2, 4)]
    clips, credits = visual_assets.build(shots, [], {"visuals": {"width": 320, "height": 180, "fps": 25}}, tmp_path)
    assert set(clips) == {1} and credits == []
    assert shots[1].notes == ["no stock key"]


# ── editor (needs ffmpeg and Chromium) ───────────────────────────────────────
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


def test_apply_reviewed_keeps_a_directed_copy_of_the_same_words(tmp_path, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location("apply_reviewed", Path(__file__).parents[1] / "scripts" / "apply_reviewed.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "reviewed" / "w").mkdir(parents=True)
    (tmp_path / "reviewed" / "w" / "script.md").write_text(SCRIPT, encoding="utf-8")
    out = tmp_path / "output" / "w" / "script.md"
    assert mod.main("w") == "using reviewed script"                      # nothing there yet
    out.write_text(director.auto_direct(SCRIPT), encoding="utf-8")
    assert mod.main("w") == "kept the directed copy of the reviewed script"
    assert "[Face]" in out.read_text(encoding="utf-8")
    (tmp_path / "reviewed" / "w" / "script.md").write_text(SCRIPT + "\nجملة جديدة.", encoding="utf-8")
    assert mod.main("w") == "using reviewed script"                      # a new edit wins
    assert "[Face]" not in out.read_text(encoding="utf-8")


def test_strip_shots_removes_only_shot_markers():
    from pipeline.script_format import strip_shots
    directed = director.auto_direct(SCRIPT)
    stripped = strip_shots(directed)
    assert not extract_shots(stripped)
    assert "[Section: الافتتاحية]" in stripped and "[Pause]" in stripped and "[On-Screen Text: 80%]" in stripped
    assert spoken_text(stripped).split() == spoken_text(SCRIPT).split()


def test_adjacent_face_markers_are_one_shot():
    script = "[Face]\nواحد اتنين.\n[Face]\nتلاتة أربعة.\n[Visual: title عنوان]\nخمسة ستة."
    shots = visuals.plan(script, 9.0, None)
    assert [s.mode for s in shots] == ["face", "visual"]


def test_shot_list_names_sources_by_headline():
    shots = [visuals.Shot("visual", "source", "abc", 0, 5)]
    md = visuals.shotlist_md(shots, visuals.lint(shots, {}), False, {"abc": "ET Datacenters: G42 in Greece"})
    assert "ET Datacenters: G42 in Greece" in md and "| abc |" not in md


def test_pixabay_prefers_animations(monkeypatch):
    calls = []
    def fake(query, key, per_page, video_type):
        calls.append(video_type)
        return [{"id": f"pixabay_{video_type}", "animation": video_type == "animation", "duration": 10, "width": 1920,
                 "video_files": [{"file_type": "video/mp4", "width": 1920, "height": 1080, "link": video_type}]}]
    monkeypatch.setattr(visual_assets, "_pixabay", fake)
    vids = visual_assets.pixabay_search("neural network", "k")
    assert calls == ["animation", "film"] and vids[0]["animation"]


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_tech_motion_frames_move(tmp_path):
    if not _chromium_ok():
        pytest.skip("needs Chromium")
    with visual_assets.Renderer(160, 90) as r:
        n = r.tech_motion("data centre", tmp_path, 1.0, fps=4)
    frames = sorted(tmp_path.glob("f*.png"))
    assert n == 4 and len(frames) == 4
    assert frames[0].read_bytes() != frames[-1].read_bytes()   # it actually moves


def test_director_gets_one_round_of_screen_time_feedback():
    words = " ".join(["كلمة"] * 40) + "."
    all_visual = f"[Visual: title عنوان]\n{words}\n[Visual: title تاني]\n{words}"
    balanced = f"[Face]\n{words}\n[Visual: title عنوان]\n{words}\n[Visual: title تاني]\n{words}\n[Visual: title تالت]\n{words}\n[Visual: title رابع]\n{words}\n[Visual: title خامس]\n{words}"
    script = "\n".join([words] * 2)
    client = FakeClient([all_visual, all_visual])
    cfg = {"scripting": {"model": "m", "words_per_minute": 130}, "visuals": {"face_share": [0.1, 0.2]}}
    out = director.direct(script, [], cfg, client)
    assert client.calls == 2 and out == all_visual.strip()          # feedback sent once, then accepted
    script6 = "\n".join([words] * 6)
    client = FakeClient([balanced])
    assert director.direct(script6, [], cfg, client) == balanced.strip() and client.calls == 1


def test_fallback_keeps_the_face_the_exception_without_cues():
    plain = "[Section: خبر]\n" + "\n".join(f"جملة رقم {i} عن الذكاء الاصطناعي بالمنطقة." for i in range(12))
    out = director.auto_direct(plain)
    assert spoken_text(out).split() == spoken_text(plain).split()
    report = visuals.lint(visuals.plan(out, 60.0), {})
    assert report["face_share"] <= 0.25 and report["kinds"]["stock"] >= 8
