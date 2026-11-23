"""Automatic face clips (pipeline/video/faces.py): paid per second, so never twice for one clip and never started
on a wallet that cannot finish the episode."""
import pytest
import yaml

from pipeline.video import faces


class R:
    def __init__(self, code, data=None, text=""):
        self.status_code, self._d, self.text, self.ok = code, data, text, code == 200

    def json(self):
        return self._d


class Http:
    def __init__(self, posts=(), gets=()):
        self.posts, self.gets, self.calls = list(posts), list(gets), []

    def post(self, url, **kw):
        self.calls.append(("POST", url, kw))
        return self.posts.pop(0)

    def get(self, url, **kw):
        self.calls.append(("GET", url, kw))
        return self.gets.pop(0)


CFG = {"video": {"heygen": {"face_image": "assets/p.png", "face_usd_per_second": 0.04, "face_budget_margin": 1.25}}}
CHUNKS = [{"id": "01-face", "role": "face", "text": "Hi."}, {"id": "02-voice", "role": "voice", "text": "News."},
          {"id": "03-face", "role": "face", "text": "Bye."}]


def voice_file(tmp_path, **over):
    data = {"01-face": {"audio": "https://a/1.wav", "duration": 10.0}, "02-voice": {"audio": "https://a/2.wav", "duration": 60.0},
            "03-face": {"audio": "https://a/3.wav", "duration": 5.0}}
    data.update(over)
    p = tmp_path / "voice.yaml"
    p.write_text(yaml.safe_dump(data), encoding="utf-8")
    return p


def test_balance_reads_a_usd_wallet_and_nothing_else():
    ok = Http(gets=[R(200, {"data": {"billing_type": "wallet", "wallet": {"currency": "usd", "remaining_balance": 1.28}}})])
    assert faces.balance("k", http=ok) == 1.28
    assert ok.calls[0][2]["headers"]["X-Api-Key"] == "k"
    assert faces.balance("k", http=Http(gets=[R(200, {"data": {"billing_type": "subscription"}})])) is None
    assert faces.balance("k", http=Http(gets=[R(401, text="no")])) is None


def test_make_face_sends_image_and_audio_once_and_waits_for_the_clip():
    http = Http(posts=[R(200, {"data": {"video_id": "v1", "status": "waiting"}})],
                gets=[R(200, {"data": {"status": "processing"}}), R(200, {"data": {"status": "completed", "video_url": "https://v/1.mp4"}})])
    waits = []
    assert faces.make_face("https://i/p.png", "https://a/1.wav", "k", http=http, sleep=waits.append) == "https://v/1.mp4"
    _, url, kw = http.calls[0]
    assert url == faces.BASE + "/v3/videos" and kw["json"]["type"] == "image" and kw["json"]["audio_url"] == "https://a/1.wav"
    assert kw["json"]["image"] == {"type": "url", "url": "https://i/p.png"}
    assert len(waits) == 2 and sum(c[0] == "POST" for c in http.calls) == 1
    # the same clip asked for again carries the same key, so HeyGen does not make (and charge) it twice
    again = Http(posts=[R(200, {"data": {"video_id": "v1"}})], gets=[R(200, {"data": {"status": "completed", "video_url": "u"}})])
    faces.make_face("https://i/p.png", "https://a/1.wav", "k", http=again, sleep=lambda s: None)
    assert again.calls[0][2]["headers"]["Idempotency-Key"] == kw["headers"]["Idempotency-Key"]


def test_make_face_reports_a_failed_clip_and_a_refused_request():
    bad = Http(posts=[R(200, {"data": {"video_id": "v1"}})],
               gets=[R(200, {"data": {"status": "failed", "failure_code": "x", "failure_message": "no face found"}})])
    with pytest.raises(RuntimeError, match="no face found"):
        faces.make_face("i", "a", "k", http=bad, sleep=lambda s: None)
    with pytest.raises(RuntimeError, match="402"):
        faces.make_face("i", "a", "k", http=Http(posts=[R(402, text="insufficient_credit")]), sleep=lambda s: None)


def test_face_week_makes_only_the_missing_face_clips_and_saves_each(tmp_path):
    p = voice_file(tmp_path)
    made = []
    faces.face_week(p, CHUNKS, CFG, "https://raw/x/main", key="k", balance_fn=lambda k: 5.0,
                    make_fn=lambda img, audio, key: made.append((img, audio)) or f"https://v/{len(made)}.mp4")
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    assert made == [("https://raw/x/main/assets/p.png", "https://a/1.wav"), ("https://raw/x/main/assets/p.png", "https://a/3.wav")]
    assert data["01-face"]["video"] == "https://v/1.mp4" and data["03-face"]["video"] == "https://v/2.mp4"
    assert "video" not in data["02-voice"] and data["01-face"]["video_at"]
    made.clear()   # a second run: nothing left to make, nothing paid
    faces.face_week(p, CHUNKS, CFG, "https://raw/x/main", key="k", balance_fn=lambda k: 0.0, make_fn=lambda *a: made.append(a))
    assert made == []


def test_face_week_refuses_before_spending_when_the_wallet_cannot_cover_it(tmp_path):
    p = voice_file(tmp_path)
    made = []
    with pytest.raises(faces.WalletShort, match="0.75") as e:   # 15 s x 0.04 x 1.25
        faces.face_week(p, CHUNKS, CFG, "https://raw/x/main", key="k", balance_fn=lambda k: 0.5, make_fn=lambda *a: made.append(a))
    assert made == [] and "0.50" in str(e.value)


def test_face_week_keeps_a_paid_clip_when_a_later_one_fails(tmp_path):
    p = voice_file(tmp_path)

    def make(img, audio, key):
        if audio.endswith("3.wav"):
            raise RuntimeError("HTTP 500")
        return "https://v/1.mp4"
    with pytest.raises(RuntimeError, match="500"):
        faces.face_week(p, CHUNKS, CFG, "https://raw/x/main", key="k", balance_fn=lambda k: 5.0, make_fn=make)
    assert yaml.safe_load(p.read_text(encoding="utf-8"))["01-face"]["video"] == "https://v/1.mp4"


def test_face_week_remakes_a_clip_whose_link_has_expired(tmp_path):
    p = voice_file(tmp_path, **{"01-face": {"audio": "https://a/1.wav", "duration": 10.0, "video": "https://old", "video_at": "2026-11-01T00:00:00Z"},
                                "03-face": {"audio": "https://a/3.wav", "duration": 5.0, "video": "https://fresh", "video_at": "2026-11-22T00:00:00Z"}})
    from datetime import datetime, timezone
    made = []
    faces.face_week(p, CHUNKS, CFG, "https://raw/x/main", key="k", balance_fn=lambda k: 5.0,
                    make_fn=lambda img, audio, key: made.append(audio) or "https://new", now=datetime(2026, 11, 23, tzinfo=timezone.utc))
    assert made == ["https://a/1.wav"]


def test_cost_is_seconds_times_the_measured_rate():
    assert faces.cost(53.7, CFG) == pytest.approx(53.7 * 0.04)


def test_the_engine_comparison_keeps_one_picture_and_sound_per_language():
    from scripts import heygen_cost as hc
    vs = hc.variants("https://x/face.png", {"en": "https://x/en.wav", "ar": "https://x/ar.wav"})
    assert [v["name"] for v in vs if v["lang"] == "ar"] == ["ar avatar-iv (today)", "ar avatar-6", "ar avatar-iv + precision lip-sync"]
    videos = [v for v in vs if v["kind"] == "video"]
    assert all(v["body"]["audio_url"] == f"https://x/{v['lang']}.wav" and v["body"]["image"]["url"] == "https://x/face.png" for v in videos)
    assert "engine" not in videos[0]["body"] and videos[1]["body"]["engine"] == {"type": "heygen-avatar-6"}
    assert sum("motion_prompt" in v["body"] for v in videos) == 1
    assert all(v["of"] in {x["name"] for x in videos} for v in vs if v["kind"] == "lipsync")
