"""ElevenLabs sound effects at the section cuts (founder 2026-11-21: "for 11 labs and the sound effects, put them
in this episode"). Generated once in GitHub Actions, committed under assets/sfx/, rotated across the cuts."""
import shutil
import subprocess

import pytest

from pipeline.post import audio, sfx

ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")


class Http:
    def __init__(self, body):
        self.body, self.calls = body, []

    def post(self, url, json=None, headers=None, timeout=None):
        self.calls.append((url, json, headers))
        body = self.body

        class R:
            content = body
            status_code = 200

            def raise_for_status(self):
                pass
        return R()


@ffmpeg
def test_generate_asks_elevenlabs_once_per_missing_sound_and_levels_it(tmp_path):
    mp3 = tmp_path / "src.mp3"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "anoisesrc=d=1:a=0.5", str(mp3)], check=True)
    http = Http(mp3.read_bytes())
    items = [{"name": "swoosh_a", "prompt": "soft airy whoosh", "seconds": 1.0},
             {"name": "swoosh_b", "prompt": "digital swoosh", "seconds": 1.2}]
    out = tmp_path / "sfx"
    (out).mkdir()
    (out / "swoosh_b.wav").write_bytes(b"kept")
    got = sfx.generate(items, out, key="k", http=http)
    assert [p.name for p in got] == ["swoosh_a.wav", "swoosh_b.wav"]
    assert len(http.calls) == 1
    url, body, headers = http.calls[0]
    assert url == sfx.API and body["text"] == "soft airy whoosh" and body["duration_seconds"] == 1.0
    assert headers["xi-api-key"] == "k"
    assert abs(sfx.rms(out / "swoosh_a.wav") - audio.WHOOSH_RMS) < 0.02


def test_cut_sounds_rotate_committed_files_else_the_synthesised_whoosh(tmp_path):
    work = tmp_path / "work"
    assert [p.name for p in sfx.cut_sounds(tmp_path / "none", work)] == ["whoosh.wav"]
    d = tmp_path / "sfx"
    d.mkdir()
    for n in ("b", "a"):
        (d / f"{n}.wav").write_bytes(b"x")
    assert [p.name for p in sfx.cut_sounds(d, work)] == ["a.wav", "b.wav"]


def test_settings_list_the_sounds_and_master_uses_them():
    import inspect
    import yaml
    a = yaml.safe_load(open("config/settings.yaml"))["post"]["audio"]
    assert a["sfx_dir"] == "assets/sfx" and len(a["sfx"]) >= 3
    assert "cut_sounds" in inspect.getsource(audio.master)
