"""Founder rules from the W47-en review (2026-11-20), for every episode from W48:
1. introduce the host by name and bio, with his face;  2. no story repeated from earlier episodes unless something
substantially new happened;  3. Africa and Türkiye get a seat when they have AI news."""
import json
from datetime import datetime, timedelta, timezone

from pipeline.ingestion import scoring
from pipeline.models import NewsItem
from pipeline.script_format import ensure_host_intro

AR_LINE = "معكم وسام كيشك. صرلي خمسة وعشرين سنة بالبرمجيات المؤسسية، بالشرق الأوسط وتركيا وأفريقيا."
EN_LINE = "I'm Wissam Kishek. I've spent 25 years in enterprise software, across the Middle East, Türkiye and Africa."


def test_host_intro_is_added_when_the_welcome_only_says_the_first_name():
    s = "[Section: الترحيب]\n[Face]\nأهلا فيكم بـ«أسبوع الذكاء الاصطناعي»، معكم وسام.\n\n[Section: قصة]\nنص.\n"
    out = ensure_host_intro(s, AR_LINE, lang="ar")
    assert AR_LINE in out and "معكم وسام." not in out and out.count("كيشك") == 1


def test_host_intro_left_alone_when_present_and_added_in_english():
    s = f"[Section: Welcome]\n[Face]\nHi everyone, welcome to AI This Week. {EN_LINE}\n"
    assert ensure_host_intro(s, EN_LINE, lang="en") == s
    s2 = "[Section: Welcome]\n[Face]\nHi everyone, welcome to AI This Week. I'm Wissam.\n"
    assert EN_LINE in ensure_host_intro(s2, EN_LINE, lang="en")


def item(title, source, region="", hours=10, summary="enterprise adoption of AI agents on the cloud"):
    return NewsItem(source=source, source_type="rss", title=title, summary=summary, url=f"https://x/{source}/{title}",
                    published=datetime.now(timezone.utc) - timedelta(hours=hours), track="models", region=region)


CFG = {"scoring": {"min_score": 0.5, "max_items": 4, "dedupe_similarity": 0.82,
                   "min_per_region": {"africa": 1, "turkey": 1}}}


def test_africa_and_turkey_each_get_a_seat_when_they_have_news():
    heads = ["OpenAI ships agent platform", "Google cuts Gemini prices", "Nvidia books record quarter",
             "Microsoft expands Copilot seats", "Amazon opens Bedrock region", "Meta trains new Llama"]
    strong = [item(h, f"Src{k}") for k, h in enumerate(heads)]
    africa = item("Cassava seeks $1 billion for AI data centres in Africa", "TechCabal", summary="")
    turkey = item("Türkiye considers labels for AI-generated content", "Hürriyet Daily News", summary="")
    kept = scoring.rank_and_filter(strong + [africa, turkey], CFG)
    assert africa in kept and turkey in kept and len(kept) == 4


def test_a_story_from_an_earlier_episode_is_marked_down():
    covered = ["Anthropic IPO is largest in history, overtaking SpaceX"]
    old = item("Anthropic IPO shares rise again after record debut", "CNBC")
    fresh = item("Gemini 4 Neon launches for enterprise agents", "Reuters")
    kept = scoring.rank_and_filter([old, fresh], {"scoring": {**CFG["scoring"], "min_per_region": {}}}, covered=covered)
    assert kept[0] is fresh and old.score_breakdown["repeat"] < 0


def test_covered_titles_are_recorded_per_week(tmp_path):
    from pipeline.ingestion import covered as cov
    f = tmp_path / "covered.json"
    cov.record(f, "2026-W47", ["A story", "B story"])
    cov.record(f, "2026-W48", ["C story"])
    cov.record(f, "2026-W47", ["A story v2"])                      # a re-run replaces its week
    assert json.loads(f.read_text())["2026-W47"] == ["A story v2"]
    assert cov.recent(f, "2026-W49", weeks=4) == ["A story v2", "C story"]
    assert cov.recent(f, "2026-W48", weeks=4) == ["A story v2"]    # never the week itself


def test_assemble_refuses_a_face_chunk_without_a_face_video():
    from pipeline.video.voicefirst import missing_faces
    chunks = [{"id": "01-face", "role": "face", "text": "Hi"}, {"id": "02-voice", "role": "voice", "text": "x"}]
    assert missing_faces({"01-face": "https://a/1.wav", "02-voice": "https://a/2.wav"}, chunks) == ["01-face"]
    assert missing_faces({"01-face": {"audio": "https://a", "video": "https://v"}, "02-voice": "https://a"}, chunks) == []
