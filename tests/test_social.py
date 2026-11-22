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
    monkeypatch.setattr(social.TikTok, "SINGLE", 20)
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


def test_post_due_never_reposts_when_the_platform_may_already_have_the_video(tmp_path):
    """2026-11-17: TikTok took the upload, the run then errored, and the retry posted the Short a second time."""
    q = []
    social.plan_week(week(tmp_path, 1), CFG, q, lambda f: f, datetime(2026, 11, 15, tzinfo=timezone.utc))
    q[0]["approved"] = True
    calls = []

    def maybe(e, f):
        calls.append(e["id"])
        raise social.Unconfirmed("TikTok publish P: still PROCESSING_UPLOAD", ref="P")
    now = datetime(2026, 11, 30, tzinfo=timezone.utc)
    lines = social.post_due(q, CFG, lambda e: Path("x.mp4"), {"tiktok": maybe}, now)
    r = q[0]["posts"]["tiktok"]
    assert r["status"] == "unconfirmed" and r["ref"] == "P" and lines[0].startswith("⚠️")
    social.post_due(q, CFG, lambda e: Path("x.mp4"), {"tiktok": maybe}, now)
    assert calls == ["2026-W45-en#1"]                                             # never sent a second time


def test_tiktok_status_timeout_after_upload_is_unconfirmed_not_failed(tmp_path):
    f = tmp_path / "v.mp4"
    f.write_bytes(b"x" * 5)
    http = FakeHttp({
        ("POST", "creator_info"): {"data": {"privacy_level_options": ["PUBLIC_TO_EVERYONE"]}, "error": {"code": "ok"}},
        ("POST", "video/init"): {"data": {"publish_id": "P", "upload_url": "https://up/1"}, "error": {"code": "ok"}},
        ("PUT", "https://up/1"): ({}, 201),
        ("POST", "status/fetch"): {"data": {"status": "PROCESSING_UPLOAD"}, "error": {"code": "ok"}}})
    with pytest.raises(social.Unconfirmed) as exc:
        social.TikTok("tok", http=http, sleep=lambda s: None).post_video(f, "caption", wait_s=0)
    assert exc.value.ref == "P"


def test_tiktok_failed_upload_before_tiktok_has_it_stays_retryable(tmp_path):
    f = tmp_path / "v.mp4"
    f.write_bytes(b"x" * 5)
    http = FakeHttp({
        ("POST", "creator_info"): {"data": {"privacy_level_options": ["PUBLIC_TO_EVERYONE"]}, "error": {"code": "ok"}},
        ("POST", "video/init"): {"data": {"publish_id": "P", "upload_url": "https://up/1"}, "error": {"code": "ok"}},
        ("PUT", "https://up/1"): ({}, 500)})
    with pytest.raises(RuntimeError) as exc:
        social.TikTok("tok", http=http, sleep=lambda s: None).post_video(f, "caption")
    assert not isinstance(exc.value, social.Unconfirmed)


def test_merge_posts_keeps_this_runs_results_over_a_concurrent_queue_change():
    """2026-11-17: the queue save hit a git conflict and the 'posted' record was lost, so the next run reposted."""
    remote = [{"id": "A", "approved": True, "posts": {"tiktok": {"status": "queued"}, "youtube": {"status": "posted"}}},
              {"id": "B", "approved": False, "posts": {"tiktok": {"status": "queued"}}}]
    ours = [{"id": "A", "approved": False, "posts": {"tiktok": {"status": "posted", "attempts": 1, "at": "t"},
                                                     "youtube": {"status": "posted"}}}]
    merged = social.merge_posts(remote, ours)
    assert merged[0]["posts"]["tiktok"] == {"status": "posted", "attempts": 1, "at": "t"}   # our result kept
    assert merged[0]["approved"] is True and [e["id"] for e in merged] == ["A", "B"]      # their changes kept
    remote[0]["posts"]["tiktok"] = {"status": "posted", "attempts": 2, "at": "later"}
    assert social.merge_posts(remote, ours)[0]["posts"]["tiktok"]["at"] == "later"       # never go back in time


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


def test_linkedin_caption_links_the_channel_and_caps_tags_at_ten(tmp_path):
    cfg = {"publish": {"hashtags_en": [f"#T{i}" for i in range(12)]},
           "social": {"channel_url": "https://www.youtube.com/@AIThisWeekME",
                      "platforms": ["linkedin", "tiktok"], "require_approval": True}}
    q = []
    social.plan_week(week(tmp_path, 1), cfg, q, lambda f: f, datetime(2026, 11, 15, tzinfo=timezone.utc))
    li, tt = q[0]["captions"]["linkedin"], q[0]["captions"]["tiktok"]
    assert "Full episode: https://www.youtube.com/@AIThisWeekME" in li and "link in bio" in tt
    assert li.count("#") == 10 and "linkedin" in q[0]["posts"]   # broad tags, capped (founder 2026-11-18)


def test_tiktok_sends_a_file_under_the_single_chunk_limit_whole(tmp_path, monkeypatch):
    """W46-en: a 15 MB Short sent as one chunk declared 10 MB was refused ("The chunk size is invalid")."""
    monkeypatch.setattr(social.TikTok, "CHUNK", 10)
    monkeypatch.setattr(social.TikTok, "SINGLE", 64)
    f = tmp_path / "v.mp4"
    f.write_bytes(b"x" * 15)
    http = FakeHttp({
        ("POST", "creator_info"): {"data": {"privacy_level_options": ["SELF_ONLY"]}, "error": {"code": "ok"}},
        ("POST", "video/init"): {"data": {"publish_id": "P", "upload_url": "https://up/1"}, "error": {"code": "ok"}},
        ("PUT", "https://up/1"): ({}, 201),
        ("POST", "status/fetch"): {"data": {"status": "PUBLISH_COMPLETE"}, "error": {"code": "ok"}}})
    social.TikTok("tok", http=http, sleep=lambda s: None).post_video(f, "caption")
    init = next(kw for m, u, kw in http.calls if "video/init" in u)["json"]
    assert init["source_info"] == {"source": "FILE_UPLOAD", "video_size": 15, "chunk_size": 15, "total_chunk_count": 1}
    assert [kw["headers"]["Content-Range"] for m, u, kw in http.calls if m == "PUT"] == ["bytes 0-14/15"]


def test_tiktok_drafts_mode_sends_the_short_to_the_inbox_with_the_caption_to_paste(tmp_path):
    """2026-11-20: an unaudited app may post only to private accounts, and @aithisweek is public. Drafts land in the
    founder's TikTok inbox; he pastes the caption and taps Post in the app."""
    f = tmp_path / "v.mp4"
    f.write_bytes(b"x" * 5)
    http = FakeHttp({
        ("POST", "inbox/video/init"): {"data": {"publish_id": "P", "upload_url": "https://up/1"}, "error": {"code": "ok"}},
        ("PUT", "https://up/1"): ({}, 201),
        ("POST", "status/fetch"): {"data": {"status": "SEND_TO_USER_INBOX"}, "error": {"code": "ok"}}})
    res = social.TikTok("tok", http=http, sleep=lambda s: None).post_video(f, "Title\n\n#AI", mode="inbox")
    assert res["status"] == "SEND_TO_USER_INBOX" and res["privacy"] == "draft"
    assert "Title" in res["note"] and "#AI" in res["note"]
    init = next(kw for m, u, kw in http.calls if "inbox/video/init" in u)["json"]
    assert set(init) == {"source_info"}                       # drafts take no post settings
    assert not any("creator_info" in u for _, u, _ in http.calls)


# ── Buffer: Instagram and the Facebook Page through a publishing service (founder 2026-11-22) ───────────────
ORGS = {"data": {"account": {"organizations": [{"id": "org1", "name": "AI This Week"}]}}}
CHANNELS = {"data": {"channels": [{"id": "ch-ig", "name": "aithisweekme", "service": "instagram"},
                                  {"id": "ch-fb", "name": "AI This Week", "service": "facebook"}]}}


def _created(pid="p1"):
    return {"data": {"createPost": {"post": {"id": pid, "status": "sending"}}}}


def _status(status, **more):
    return {"data": {"post": {"id": "p1", "status": status, "externalLink": None, "error": None, **more}}}


def _buffer(*responses):
    http = FakeHttp({("POST", "api.buffer.com"): [ORGS, CHANNELS, *responses]})
    return social.Buffer("key", http=http, sleep=lambda s: None), http


def _input(http, n=2):
    return http.calls[n][2]["json"]["variables"]["input"]


def test_buffer_posts_a_reel_now_and_waits_until_it_is_live():
    bf, http = _buffer(_created(), _status("sending"), _status("sent", externalLink="https://instagram.com/reel/X"))
    res = bf.post("instagram", "Caption", video_url="https://example.com/a.mp4")
    assert res == {"buffer_id": "p1", "url": "https://instagram.com/reel/X", "via": "buffer"}
    sent = _input(http)
    assert sent["channelId"] == "ch-ig" and sent["mode"] == "shareNow" and sent["schedulingType"] == "automatic"
    assert sent["assets"] == [{"video": {"url": "https://example.com/a.mp4"}}]
    assert sent["metadata"] == {"instagram": {"type": "reel", "shouldShareToFeed": True, "isAiGenerated": True}}
    assert all(c[2]["headers"]["Authorization"] == "Bearer key" for c in http.calls)


def test_buffer_facebook_video_is_a_reel_and_a_link_is_a_link_post():
    bf, http = _buffer(_created(), _status("sent"), _created(), _status("sent"))
    bf.post("facebook", "Clip", video_url="https://example.com/a.mp4")
    assert _input(http)["metadata"] == {"facebook": {"type": "reel"}}
    bf.post("facebook", "Episode text", link="https://youtu.be/abc")
    sent = _input(http, 4)                       # the channel list is read once, not per post
    assert sent["assets"] == [] and sent["text"] == "Episode text"
    assert sent["metadata"] == {"facebook": {"type": "post", "linkAttachment": {"url": "https://youtu.be/abc"}}}


def test_buffer_refusal_is_a_plain_failure_that_may_be_retried():
    bf, _ = _buffer({"data": {"createPost": {"message": "Posting limit reached"}}})
    with pytest.raises(RuntimeError, match="Posting limit reached") as exc:
        bf.post("instagram", "x", video_url="https://example.com/a.mp4")
    assert not isinstance(exc.value, social.Unconfirmed)


def test_buffer_publishing_error_and_api_errors_are_raised():
    bf, _ = _buffer(_created(), _status("error", error={"message": "Instagram rejected the video"}))
    with pytest.raises(RuntimeError, match="Instagram rejected the video"):
        bf.post("instagram", "x", video_url="https://example.com/a.mp4")
    http = FakeHttp({("POST", "api.buffer.com"): [{"errors": [{"message": "Unauthorized"}]}]})
    with pytest.raises(RuntimeError, match="Unauthorized"):
        social.Buffer("bad", http=http, sleep=lambda s: None).post("facebook", "x", link="https://youtu.be/a")


def test_buffer_still_sending_at_the_deadline_is_unconfirmed_not_failed():
    bf, _ = _buffer(_created(), *[_status("sending") for _ in range(4)])
    with pytest.raises(social.Unconfirmed) as exc:
        bf.post("instagram", "x", video_url="https://example.com/a.mp4", wait_s=30)
    assert exc.value.ref == "p1"


def test_buffer_needs_exactly_one_connected_channel_per_platform():
    http = FakeHttp({("POST", "api.buffer.com"): [ORGS, {"data": {"channels": [
        {"id": "ch-ig", "name": "a", "service": "instagram"}]}}]})
    with pytest.raises(RuntimeError, match="facebook.*not connected in Buffer"):
        social.Buffer("key", http=http, sleep=lambda s: None).post("facebook", "x", link="https://youtu.be/a")


def test_buffer_carries_instagram_and_facebook_only_when_their_own_tokens_are_missing(monkeypatch):
    for k in ("INSTAGRAM_TOKEN", "FACEBOOK_PAGE_ID", "FACEBOOK_PAGE_TOKEN", "BUFFER_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    cfg = {**CFG, "social": {**CFG["social"], "platforms": ["instagram", "facebook"]}}
    assert social.posters(cfg) == {}
    monkeypatch.setenv("BUFFER_API_KEY", "key")
    calls = []
    monkeypatch.setattr(social.Buffer, "post", lambda self, service, text, **kw: calls.append((service, text, kw)) or {"via": "buffer"})
    made = social.posters(cfg)
    entry = {"url": "https://example.com/a.mp4", "title": "Clip", "captions": {"instagram": "IG text", "facebook": "FB text"}}
    assert made["instagram"](entry, None) == {"via": "buffer"} and made["facebook"](entry, None) == {"via": "buffer"}
    assert calls == [("instagram", "IG text", {"video_url": "https://example.com/a.mp4"}),
                     ("facebook", "FB text", {"video_url": "https://example.com/a.mp4"})]
    monkeypatch.setenv("FACEBOOK_PAGE_ID", "1")
    monkeypatch.setenv("FACEBOOK_PAGE_TOKEN", "t")
    calls.clear()
    monkeypatch.setattr(social.FacebookPage, "post_reel", lambda self, url, text, **kw: "v9")
    assert social.posters(cfg)["facebook"](entry, None)["video_id"] == "v9" and calls == []
