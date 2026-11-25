"""scripts/channel_trailer.py: upload the trailer and make it the channel trailer (founder 2026-11-25)."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("channel_trailer", Path(__file__).resolve().parents[1] / "scripts" / "channel_trailer.py")
ct = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ct)


def test_the_trailer_is_public_disclosed_and_titled_within_limits():
    body = ct.video_body({"publish": {"tags_en": ["AI", "news"]}})
    s = body["snippet"]
    assert len(s["title"]) <= 100 and "AI This Week" in s["title"]
    assert "digital twin" in s["description"] and "consent" in s["description"]
    assert body["status"] == {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}
    assert s["defaultLanguage"] == "en" and s["tags"] == ["AI", "news"]


def test_setting_the_trailer_keeps_the_rest_of_the_branding():
    branding = {"channel": {"title": "AI This Week", "keywords": "AI"}, "image": {"bannerExternalUrl": "https://b"}}
    out = ct.with_trailer(branding, "abc123")
    assert out["channel"] == {"title": "AI This Week", "keywords": "AI", "unsubscribedTrailer": "abc123"}
    assert out["image"] == {"bannerExternalUrl": "https://b"}
    assert branding["channel"].get("unsubscribedTrailer") is None      # the input is not changed
