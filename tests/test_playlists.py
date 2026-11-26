"""Topic playlists and the first comment (pipeline/publish/playlists.py, founder 2026-11-26)."""
import json

from pipeline.publish import playlists as pl

CFG = {"publish": {"playlists": [
    {"title": "Weekly", "kinds": ["episode"]},
    {"title": "Shorts", "kinds": ["short"]},
    {"title": "Gulf", "match": ["UAE", "G42", "e&"]},
    {"title": "Chips", "match": ["NVIDIA", "chip"]}]}}


def test_pick_by_kind_and_words():
    assert pl.pick("ADNOC and G42 sign a deal", "", "episode", CFG) == ["Weekly", "Gulf"]
    assert pl.pick("Jensen Huang Is Back", "NVIDIA's board reinstated him", "short", CFG) == ["Shorts", "Chips"]
    assert pl.pick("Stc and e& results", "", "short", CFG) == ["Shorts", "Gulf"]
    # hashtags and anything after the first paragraph do not count
    assert pl.pick("CIA hit by breach", "A breach.\n\n#NVIDIA #UAE\nSources: G42 blog", "short", CFG) == ["Shorts"]


class FakeYT:
    def __init__(self, lists=None, items=None):
        self.lists, self.items, self.calls = dict(lists or {}), set(items or ()), []

    def playlists(self):
        yt = self

        class P:
            def list(self, **kw):
                return type("R", (), {"execute": lambda s: {"items": [{"id": i, "snippet": {"title": t}}
                                                                      for t, i in yt.lists.items()]}})()

            def insert(self, part, body):
                t = body["snippet"]["title"]
                yt.lists[t] = f"PL{len(yt.lists)}"
                yt.calls.append(("create", t))
                return type("R", (), {"execute": lambda s: {"id": yt.lists[t]}})()
        return P()

    def playlistItems(self):
        yt = self

        class I:
            def list(self, playlistId, videoId, **kw):
                hit = (playlistId, videoId) in yt.items
                return type("R", (), {"execute": lambda s: {"items": [1] if hit else []}})()

            def insert(self, part, body):
                sn = body["snippet"]
                yt.items.add((sn["playlistId"], sn["resourceId"]["videoId"]))
                yt.calls.append(("add", sn["playlistId"]))
                return type("R", (), {"execute": lambda s: {}})()
        return I()


def test_place_creates_missing_lists_and_skips_videos_already_in():
    yt = FakeYT(lists={"Shorts": "PLs"}, items={("PLs", "v1")})
    got = pl.place(yt, "v1", "NVIDIA news", "", "short", CFG)
    assert got == ["Shorts", "Chips"]
    assert ("create", "Chips") in yt.calls and ("add", "PLs") not in yt.calls


def test_place_never_raises():
    class Broken:
        def playlists(self):
            raise RuntimeError("quota")
    assert pl.place(Broken(), "v", "NVIDIA", "", "short", CFG)[0].startswith("error:")


def test_latest_episode_and_first_comment(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "releases.json").write_text(json.dumps([
        {"video_id": "old", "status": "public", "at": "2026-11-15T13:00:00Z"},
        {"video_id": "new", "status": "public", "at": "2026-11-22T13:00:00Z"},
        {"video_id": "later", "status": "waiting", "release_at": "2026-11-29T13:00:00Z"}]))
    assert pl.latest_episode_url(tmp_path) == "https://youtu.be/new"
    text = pl.first_comment_text({"publish": {}}, "https://youtu.be/old")
    assert "matters most" in text and text.endswith("https://youtu.be/old")


def test_a_brand_new_playlist_answering_404_still_gets_the_video():
    yt = FakeYT()
    real = yt.playlistItems

    def items():
        inner = real()

        class I:
            def list(self, **kw):
                raise RuntimeError("<HttpError 404 when requesting playlistItems>")

            def insert(self, part, body):
                return inner.insert(part, body)
        return I()
    yt.playlistItems = items
    assert pl.place(yt, "v1", "NVIDIA", "", "short", CFG) == ["Shorts", "Chips"]
    assert len(yt.items) == 2
