"""Shorts / Reels / TikTok posting on the platforms' own APIs (pipeline/publish/social.py)."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pipeline.publish import social

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


class Resp:
    def __init__(self, data, status=200):
        self.data, self.status_code, self.text = data, status, json.dumps(data)

    def json(self):
        return self.data


class FakeHttp:
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def _hit(self, method, url, **kw):
        self.calls.append((method, url, kw))
        for key, val in self.routes.items():
            if key[0] == method and key[1] in url:
                return Resp(*val) if isinstance(val, tuple) else Resp(val.pop(0) if isinstance(val, list) else val)
        raise AssertionError(f"unexpected {method} {url}")

    def get(self, url, **kw):
        return self._hit("GET", url, **kw)

    def post(self, url, **kw):
        return self._hit("POST", url, **kw)

    def put(self, url, **kw):
        return self._hit("PUT", url, **kw)


CFG = {"publish": {"hashtags_en": ["#AI"], "tags_en": ["AI"]},
       "social": {"days": [0, 2, 4], "hour_utc": 15, "require_approval": True, "max_attempts": 2}}


def week(tmp_path, n=3):
    out = tmp_path / "2026-W45-en"
    (out / "shorts").mkdir(parents=True)
    (out / "shorts" / "shorts.json").write_text(json.dumps(
        [{"title": f"Clip {i}", "file": f"short_{i:02d}.mp4"} for i in range(1, n + 1)]))
    return out


def test_plan_week_spreads_clips_over_the_chosen_days_and_waits_for_approval(tmp_path):
    q = []
    start = datetime(2026, 11, 15, 10, tzinfo=timezone.utc)          # a Sunday
    new = social.plan_week(week(tmp_path), CFG, q, lambda f: f"https://x/{f}", start)
    assert [e["due"] for e in new] == ["2026-11-16T15:00:00Z", "2026-11-18T15:00:00Z", "2026-11-20T15:00:00Z"]
    assert all(not e["approved"] for e in new) and new[0]["url"] == "https://x/2026-W45-en-short-01.mp4"
    assert "#Shorts" in new[0]["captions"]["youtube"] and "#Shorts" not in new[0]["captions"]["tiktok"]
    assert "digital twin" in new[0]["captions"]["instagram"]
    assert social.plan_week(week(tmp_path / "again"), CFG, q, lambda f: f, start) == []   # never queued twice


def test_post_due_posts_only_approved_due_entries_and_retries_only_the_failed_platform(tmp_path):
    q = []
    social.plan_week(week(tmp_path, 2), CFG, q, lambda f: f, datetime(2026, 11, 15, tzinfo=timezone.utc))
    q[0]["approved"] = True
    calls = []

    def ok(e, f):
        calls.append(("yt", e["id"]))
        return {"url": "u"}

    def bad(e, f):
        calls.append(("ig", e["id"]))
        raise RuntimeError("container ERROR")
    now = datetime(2026, 11, 30, tzinfo=timezone.utc)
    lines = social.post_due(q, CFG, lambda e: Path("x.mp4"), {"youtube": ok, "instagram": bad}, now)
    assert calls == [("yt", "2026-W45-en#1"), ("ig", "2026-W45-en#1")]          # #2 is not approved
    assert q[0]["posts"]["youtube"]["status"] == "posted" and q[0]["posts"]["instagram"]["status"] == "failed"
    assert q[0]["posts"]["tiktok"]["status"] == "queued" and any(x.startswith("❌") for x in lines)
    calls.clear()
    social.post_due(q, CFG, lambda e: Path("x.mp4"), {"youtube": ok, "instagram": bad}, now)
    assert calls == [("ig", "2026-W45-en#1")]                                    # YouTube is not posted twice
    assert q[0]["posts"]["instagram"]["status"] == "skipped"                     # max_attempts reached


def test_instagram_reel_waits_for_the_container_then_publishes():
    http = FakeHttp({("GET", "/me"): {"user_id": "17841"}, ("POST", "/17841/media_publish"): {"id": "M1"},
                     ("POST", "/17841/media"): {"id": "C1"},
                     ("GET", "/C1"): [{"status_code": "IN_PROGRESS"}, {"status_code": "FINISHED"}]})
    ig = social.Instagram("tok", http=http, sleep=lambda s: None)
    assert ig.post_reel("https://x/v.mp4", "caption") == "M1"
    media = next(kw for m, u, kw in http.calls if u.endswith("/17841/media"))
    assert media["data"]["media_type"] == "REELS" and media["data"]["video_url"] == "https://x/v.mp4"


def test_instagram_container_error_is_raised():
    http = FakeHttp({("GET", "/me"): {"user_id": "1"}, ("POST", "/1/media"): {"id": "C"},
                     ("GET", "/C"): {"status_code": "ERROR"}})
    with pytest.raises(RuntimeError, match="ERROR"):
        social.Instagram("t", http=http, sleep=lambda s: None).post_reel("u", "c")


def test_tiktok_uploads_in_chunks_and_falls_back_to_private_when_unaudited(tmp_path, monkeypatch):
    monkeypatch.setattr(social.TikTok, "CHUNK", 10)
    f = tmp_path / "v.mp4"
    f.write_bytes(b"x" * 25)
    http = FakeHttp({
        ("POST", "creator_info"): {"data": {"privacy_level_options": ["SELF_ONLY"]}, "error": {"code": "ok"}},
        ("POST", "video/init"): {"data": {"publish_id": "P", "upload_url": "https://up/1"}, "error": {"code": "ok"}},
        ("PUT", "https://up/1"): ({}, 206),
        ("POST", "status/fetch"): [{"data": {"status": "PROCESSING_UPLOAD"}, "error": {"code": "ok"}},
                                   {"data": {"status": "PUBLISH_COMPLETE"}, "error": {"code": "ok"}}]})
    res = social.TikTok("tok", http=http, sleep=lambda s: None).post_video(f, "caption")
    assert res["privacy"] == "SELF_ONLY" and res["status"] == "PUBLISH_COMPLETE"
    init = next(kw for m, u, kw in http.calls if "video/init" in u)["json"]
    assert init["source_info"] == {"source": "FILE_UPLOAD", "video_size": 25, "chunk_size": 10, "total_chunk_count": 2}
    assert init["post_info"]["is_aigc"] is True
    ranges = [kw["headers"]["Content-Range"] for m, u, kw in http.calls if m == "PUT"]
    assert ranges == ["bytes 0-9/25", "bytes 10-24/25"]                          # the last chunk takes the rest


def test_tiktok_api_error_is_raised():
    http = FakeHttp({("POST", "creator_info"): {"data": {}, "error": {"code": "access_token_invalid", "message": "x"}}})
    with pytest.raises(RuntimeError, match="access_token_invalid"):
        social.TikTok("t", http=http).privacy("PUBLIC_TO_EVERYONE")


def test_connect_reads_the_code_from_a_pasted_address():
    import connect
    assert connect.code_of("http://localhost/?state=x&code=4/0Ab-c_d&scope=a") == "4/0Ab-c_d"
    assert connect.code_of("https://github.com/o/r?code=AQB12#_") == "AQB12"
    assert connect.code_of("  plaincode ") == "plaincode"


class Hdr(Resp):
    def __init__(self, data, status=200, headers=None):
        super().__init__(data, status)
        self.headers = headers or {}


def test_linkedin_uploads_in_parts_waits_for_processing_then_posts(tmp_path):
    f = tmp_path / "v.mp4"
    f.write_bytes(b"y" * 30)
    calls = []

    class Http:
        status = [{"status": "PROCESSING"}, {"status": "AVAILABLE"}]

        def get(self, url, **kw):
            calls.append(("GET", url))
            return Hdr({"sub": "abc"}) if url.endswith("/v2/userinfo") else Hdr(self.status.pop(0))

        def post(self, url, **kw):
            calls.append(("POST", url, kw.get("json")))
            if "initializeUpload" in url:
                return Hdr({"value": {"video": "urn:li:video:V", "uploadToken": "",
                                      "uploadInstructions": [{"uploadUrl": "https://up/1", "firstByte": 0, "lastByte": 19},
                                                             {"uploadUrl": "https://up/2", "firstByte": 20, "lastByte": 29}]}})
            if "finalizeUpload" in url:
                return Hdr({})
            return Hdr({}, 201, {"x-restli-id": "urn:li:share:9"})

        def put(self, url, **kw):
            calls.append(("PUT", url, len(kw["data"])))
            return Hdr({}, 200, {"ETag": f"etag-{url[-1]}"})
    res = social.LinkedIn("tok", http=Http(), sleep=lambda s: None).post_video(f, "text", "Title")
    assert res["url"] == "https://www.linkedin.com/feed/update/urn:li:share:9"
    assert [c[2] for c in calls if c[0] == "PUT"] == [20, 10]
    final = next(c[2] for c in calls if c[0] == "POST" and "finalizeUpload" in c[1])
    assert final["finalizeUploadRequest"]["uploadedPartIds"] == ["etag-1", "etag-2"]
    post = next(c[2] for c in calls if c[0] == "POST" and c[1].endswith("/rest/posts"))
    assert post["author"] == "urn:li:person:abc" and post["content"]["media"]["id"] == "urn:li:video:V"


def test_linkedin_caption_links_the_channel_and_keeps_few_tags(tmp_path):
    cfg = {"publish": {"hashtags_en": ["#A", "#B", "#C", "#D", "#E", "#F"]},
           "social": {"channel_url": "https://www.youtube.com/@aithisweekshow",
                      "platforms": ["linkedin", "tiktok"], "require_approval": True}}
    q = []
    social.plan_week(week(tmp_path, 1), cfg, q, lambda f: f, datetime(2026, 11, 15, tzinfo=timezone.utc))
    li, tt = q[0]["captions"]["linkedin"], q[0]["captions"]["tiktok"]
    assert "Full episode: https://www.youtube.com/@aithisweekshow" in li and "link in bio" in tt
    assert li.count("#") == 4 and "linkedin" in q[0]["posts"]
