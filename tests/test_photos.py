"""Real photos and generated clips (founder 2026-11-20: "use real photos of individuals related to the companies…
and more animations… digital, then real, then digital"). Photos come only from Wikimedia Commons under a licence
that allows reuse with credit; generated clips never show a real person."""
from pipeline.post import photos
from pipeline.publish.description import credits_line
from pipeline.script_format import extract_shots, parse_shot


class R:
    def __init__(self, data):
        self._d = data
        self.status_code = 200

    def json(self):
        return self._d

    def raise_for_status(self):
        pass


def page(title, lic, width=2000, artist='<a href="x">Jane Doe</a>'):
    return {"title": title, "imageinfo": [{"url": f"https://upload.wikimedia.org/{title}.jpg", "width": width,
            "thumburl": f"https://upload.wikimedia.org/thumb/{title}.jpg", "descriptionurl": f"https://commons.wikimedia.org/wiki/{title}",
            "extmetadata": {"LicenseShortName": {"value": lic}, "Artist": {"value": artist}}}]}


class Http:
    def __init__(self, pages):
        self.pages, self.params = pages, None

    def get(self, url, params=None, headers=None, timeout=None):
        self.params = params
        return R({"query": {"pages": {str(n): p for n, p in enumerate(self.pages)}}})


def test_shot_kinds_include_photo_and_generated():
    assert parse_shot("Visual: photo Dario Amodei") == ("visual", "photo", "Dario Amodei")
    assert parse_shot("Visual: generated glowing server hall at night, slow dolly") == \
        ("visual", "generated", "glowing server hall at night, slow dolly")


def test_only_reusable_licences_are_picked_and_credited():
    http = Http([page("File:Dario Amodei A.jpg", "CC BY-NC 2.0"), page("File:Dario Amodei B.jpg", "Fair use"),
                 page("File:Dario Amodei small.jpg", "CC BY 4.0", width=400), page("File:Dario Amodei C.jpg", "CC BY-SA 4.0")])
    got = photos.commons_search("Dario Amodei", http=http)
    assert got and got["title"] == "File:Dario Amodei C.jpg"
    assert got["license"] == "CC BY-SA 4.0" and got["author"] == "Jane Doe"
    assert got["provider"] == "Wikimedia Commons" and got["url"].startswith("https://commons.wikimedia.org/")
    assert "Dario Amodei" in http.params["gsrsearch"]


def test_no_reusable_photo_returns_none():
    assert photos.commons_search("Someone", http=Http([page("File:Someone A.jpg", "All rights reserved")])) is None


def test_photo_credits_name_author_and_licence():
    line = credits_line([{"provider": "Wikimedia Commons", "author": "Jane Doe", "license": "CC BY-SA 4.0"},
                         {"provider": "pixabay", "author": "Bob"}], lang="en")
    assert "Wikimedia Commons (Jane Doe, CC BY-SA 4.0)" in line and "Pixabay (Bob)" in line


def test_generation_pack_lists_generated_shots_without_a_clip():
    script = "[Visual: generated city of light at dawn, aerial]\nجملة.\n[Visual: generated server hall, dolly]\nجملة تانية.\n"
    pack = photos.generation_pack(extract_shots(script), own={"server hall, dolly": ["https://x/1.mp4"]})
    assert "city of light at dawn, aerial" in pack and "server hall" not in pack
    assert "visuals.yaml" in pack and "no real person" in pack.lower()


def test_repeated_stock_searches_are_reported():
    script = "".join(f"[Visual: stock neural network animation]\nجملة {n}.\n" for n in range(3)) + \
             "[Visual: photo Satya Nadella]\nجملة.\n"
    assert photos.variety_notes(extract_shots(script)) == [
        "stock search «neural network animation» used 3 times",
        "3 digital shots in a row before a real one (aim for no more than 2)"]


def test_a_photo_must_name_its_subject_in_the_file_title():
    """2026-11-21: "OpenAI headquarters" matched the European Southern Observatory and "Brad Gerstner" a Trump event."""
    http = Http([page("File:Welcome to ESO Headquarters.jpg", "CC BY 4.0"), page("File:OpenAI office in San Francisco.jpg", "CC BY 4.0")])
    assert photos.commons_search("OpenAI headquarters", http=http)["title"] == "File:OpenAI office in San Francisco.jpg"
    assert photos.commons_search("Brad Gerstner", http=Http([page("File:P2025 President Donald Trump.jpg", "Public domain")])) is None


def test_an_exact_commons_file_can_be_named():
    http = Http([page("File:Alibaba Center in Binjiang Hangzhou2021.jpg", "CC BY-SA 4.0")])
    got = photos.commons_search("File:Alibaba Center in Binjiang Hangzhou2021.jpg", http=http)
    assert got["title"] == "File:Alibaba Center in Binjiang Hangzhou2021.jpg" and http.params["titles"].startswith("File:Alibaba")


def test_photos_already_used_in_past_episodes_are_skipped():
    """Founder 2026-11-21: keep changing the head-office photos (different angles) from video to video."""
    http = Http([page("File:Googleplex A.jpg", "CC BY 4.0"), page("File:Googleplex B.jpg", "CC BY 4.0")])
    assert photos.commons_search("Googleplex", http=http, avoid={"File:Googleplex A.jpg"})["title"] == "File:Googleplex B.jpg"


def test_used_photos_are_recorded_per_week_and_avoided_elsewhere(tmp_path):
    """Founder 2026-11-21: vary the head-office and people photos from video to video."""
    f = tmp_path / "photos_used.json"
    photos.record_used(f, "2026-W47-en", ["File:Googleplex HQ (cropped).jpg"])
    photos.record_used(f, "2026-W48-en", ["File:NVIDIA Headquarters.jpg"])
    assert photos.used_elsewhere(f, "2026-W48-en") == {"File:Googleplex HQ (cropped).jpg"}
    assert photos.used_elsewhere(tmp_path / "missing.json", "W") == set()


def test_the_director_asks_for_people_and_head_office_photos():
    from pipeline.scripting import director
    assert "headquarters" in director.SYSTEM and "names a person" in director.SYSTEM


def test_photo_shots_carry_a_name_label_after_a_bar():
    """Founder 2026-11-21: a person's photo shows their name (and role) — the audience is the general public."""
    from pipeline.post import visual_assets as va
    assert va.photo_parts("File:Dario Amodei in 2023.jpg | Dario Amodei, CEO of Anthropic") == \
        ("File:Dario Amodei in 2023.jpg", "Dario Amodei", "CEO of Anthropic")
    assert va.photo_parts("Googleplex") == ("Googleplex", "", "")
    html = va.name_html("Dario Amodei", "CEO of Anthropic", 1920, 1080)
    assert "Dario Amodei" in html and "CEO of Anthropic" in html and "background:transparent" in html


def test_photo_clip_overlays_the_label(tmp_path):
    import subprocess
    import numpy as np
    from pipeline.post import visual_assets as va
    img, lab = tmp_path / "p.png", tmp_path / "l.png"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=gray:s=640x360", "-frames:v", "1", str(img)], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=red:s=320x180,format=rgba",
                    "-vf", "geq=r='255':g='0':b='0':a='if(gt(Y,120),255,0)'", "-frames:v", "1", str(lab)], check=True)
    out = va.photo_clip(img, 1.0, tmp_path / "o.mp4", 320, 180, 10, label=lab)
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-sseof", "-0.2", "-i", str(out), "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    px = np.frombuffer(raw, np.uint8).reshape(180, 320, 3)
    assert px[170, 160, 0] > 150 and px[170, 160, 1] < 100       # the label's red at the bottom
    assert abs(int(px[40, 160, 0]) - int(px[40, 160, 1])) < 30     # the photo's grey above it


def test_the_director_asks_for_a_name_under_every_person_photo():
    from pipeline.scripting import director
    assert "| Name, role" in director.SYSTEM
