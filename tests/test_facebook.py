from pathlib import Path

from pipeline.publish.social import FacebookPage, caption


class R:
    def __init__(self, code=200, data=None, url=""):
        self.status_code, self._d, self.url, self.text = code, data or {}, url, ""
    def json(self): return self._d


class Http:
    def __init__(self): self.calls = []
    def post(self, url, data=None, headers=None, files=None, timeout=None):
        self.calls.append(("POST", url, data, headers))
        if url.endswith("/video_reels") and data.get("upload_phase") == "start":
            return R(data={"video_id": "V1"})
        if "rupload" in url:
            return R(data={"success": True})
        if url.endswith("/videos"):
            return R(data={"id": "EP1"})
        return R(data={"success": True, "id": "P_1"})
    def get(self, url, params=None, timeout=None):
        self.calls.append(("GET", url, params, None))
        return R(data={"status": {"uploading_phase": {"status": "complete"}}})


def test_reel_is_started_fetched_and_published():
    h = Http()
    vid = FacebookPage("123", "tok", http=h, sleep=lambda s: None).post_reel("https://x/clip.mp4", "Caption")
    assert vid == "V1"
    upload = [c for c in h.calls if "rupload" in c[1]][0]
    assert upload[3]["file_url"] == "https://x/clip.mp4" and upload[3]["Authorization"] == "OAuth tok"
    finish = h.calls[-1][2]
    assert finish["upload_phase"] == "finish" and finish["video_state"] == "PUBLISHED" and finish["description"] == "Caption"


def test_episode_upload(tmp_path):
    f = tmp_path / "ep.mp4"
    f.write_bytes(b"x")
    h = Http()
    assert FacebookPage("123", "tok", http=h).post_video(f, "Title", "Text") == "EP1"
    assert "graph-video.facebook.com" in h.calls[0][1]


def test_facebook_caption_carries_the_channel_link():
    cfg = {"social": {"channel_url": "https://youtube.com/@x"}, "publish": {"hashtags_en": ["#AI"]}}
    assert "https://youtube.com/@x" in caption({"title": "T"}, cfg, "en", "facebook")


def test_captions_point_to_instagram_and_tiktok_not_the_whatsapp_channel():
    """Founder 2026-11-28: the WhatsApp Channel is no longer promoted; Instagram and TikTok are."""
    cfg = {"social": {"channel_url": "https://youtube.com/@x",
                      "follow": {"Instagram": "https://www.instagram.com/ig", "TikTok": "https://www.tiktok.com/@tt"}},
           "publish": {"hashtags_en": ["#AI"]}}
    for p in ("youtube", "linkedin", "facebook"):
        c = caption({"title": "T"}, cfg, "en", p)
        assert "Instagram: https://www.instagram.com/ig" in c and "TikTok: https://www.tiktok.com/@tt" in c, p
        assert "whatsapp" not in c.lower(), p
    for p in ("instagram", "tiktok"):                      # links are not clickable there
        assert "https://www.instagram.com/ig" not in caption({"title": "T"}, cfg, "en", p)
    ar = caption({"title": "T"}, cfg, "ar", "youtube")
    assert "تابعونا" in ar and "https://www.tiktok.com/@tt" in ar


def test_whatsapp_kit_is_for_the_status_only():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from channel import kit_body
    b = kit_body("California sues OpenAI #Shorts", "https://youtu.be/x", "https://r/clip.mp4", True, "https://yt/@c")
    assert "WhatsApp Channel" not in b and "My status" in b and "⚡ California sues OpenAI" in b and "#Shorts" not in b
    assert "https://r/clip.mp4" in b