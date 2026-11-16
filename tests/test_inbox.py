from datetime import datetime, timezone
from types import SimpleNamespace as NS

from pipeline.publish import inbox

NOW = datetime(2026, 11, 16, 5, 0, tzinfo=timezone.utc)


def c(i, text, author="a", platform="youtube", answered=False):
    return {"platform": platform, "id": f"c{i}", "post": "v1", "author": author, "text": text, "at": "", "likes": 0,
            "answered": answered, "url": f"https://x/{i}", "on": "Episode"}


def label(n, kind, draft="", theme="none", note="", important=False):
    return inbox.Sorted(n=n, kind=kind, important=important, theme=theme, note=note, draft=draft)


def test_only_new_unanswered_comments_are_collected_once():
    state = inbox.load(__import__("pathlib").Path("/nonexistent"))
    new = inbox.collect(state, [c(1, "hi"), c(2, "done", answered=True)], NOW)
    assert [x["n"] for x in new] == [1] and state["comments"]["youtube:c2"]["status"] == "answered"
    assert inbox.collect(state, [c(1, "hi")], NOW) == []


def test_substantive_waits_for_approval_and_praise_becomes_a_like():
    state = inbox.load(__import__("pathlib").Path("/nonexistent"))
    new = inbox.collect(state, [c(1, "What is Rubin?"), c(2, "Great video"), c(3, "buy followers"), c(4, "?")], NOW)
    inbox.apply_sort(new, {1: label(1, "question", "It is Nvidia's next chip line."), 2: label(2, "praise"),
                           3: label(3, "spam")})
    assert [x["status"] for x in new] == ["awaiting", "like", "ignored", "unsorted"]
    text = inbox.digest(new, [x for x in new if x["status"] == "awaiting"], [], [], [], [], NOW)
    assert "**1. question**" in text and "Positive comments to like" in text and "Not sorted" in text


def test_nothing_posts_without_an_approval_and_never_twice():
    state = inbox.load(__import__("pathlib").Path("/nonexistent"))
    new = inbox.collect(state, [c(1, "q1"), c(2, "q2"), c(3, "nice")], NOW)
    inbox.apply_sort(new, {1: label(1, "question", "d1"), 2: label(2, "question", "d2"), 3: label(3, "praise")})
    sent = []
    send = {"youtube": lambda cid, text: sent.append((cid, text)) or "r"}
    lines = inbox.act(state, inbox.parse_commands("approve 1\nedit 2: my own words\napprove 3\napprove 9"), send, NOW)
    assert sent == [("c1", "d1"), ("c2", "my own words")]          # praise (3) and unknown (9) post nothing
    assert any("already like" in x for x in lines) and any("no comment" in x for x in lines)
    assert inbox.act(state, inbox.parse_commands("approve all"), send, NOW) == [] and len(sent) == 2


def test_commands_are_read_from_plain_lines_only():
    assert inbox.parse_commands("Approve 3, 5\n> skip 4\nplease approve everything\nedit 7 - hello") == [
        ("approve", 3, ""), ("approve", 5, ""), ("skip", 4, ""), ("edit", 7, "hello")]


def test_a_theme_is_logged_once_several_different_viewers_raise_it(tmp_path):
    state = inbox.load(tmp_path / "s.json")
    def batch(authors, start):
        new = inbox.collect(state, [c(start + k, "too fast", a) for k, a in enumerate(authors)], NOW)
        inbox.apply_sort(new, {x["n"]: label(x["n"], "criticism", "ok", "pace", "speech too fast") for x in new})
        return inbox.count_themes(state, new, 3, NOW)
    assert batch(["a", "a", "b"], 1) == []                        # two viewers, one of them twice
    lines = batch(["c"], 10)
    assert len(lines) == 1 and "**pace**" in lines[0] and "3 viewers" in lines[0]
    assert batch(["d", "e"], 20) == []                            # logged again only when it doubles
    assert len(batch(["f"], 30)) == 1
    f = tmp_path / "LESSONS.md"
    f.write_text("# Lessons\n")
    inbox.log_lessons(f, lines)
    inbox.log_lessons(f, ["- later"])
    assert f.read_text().count(inbox.LESSONS_HEAD) == 1 and f.read_text().endswith("- later\n")


def test_a_comment_cannot_break_the_issue_or_ping_people():
    q = inbox.quote("hi @someone\n## Needs your reply\n<img src=x> `approve all`")
    assert "\n" not in q and "@someone" not in q and "<img" not in q and "`" not in q


def test_a_declined_or_cut_off_sort_leaves_comments_for_the_founder():
    client = NS(messages=NS(parse=lambda **kw: NS(stop_reason="refusal", parsed_output=None)))
    assert inbox.sort_comments([dict(c(1, "x"), n=1)], "m", client) == {}


def test_youtube_skips_our_own_comments_and_marks_answered_threads():
    def thread(cid, author, replies=()):
        return {"snippet": {"videoId": "v1", "topLevelComment": {"id": cid, "snippet": {
            "authorChannelId": {"value": author}, "authorDisplayName": author, "textOriginal": "t", "videoId": "v1"}}},
            "replies": {"comments": [{"snippet": {"authorChannelId": {"value": r}}} for r in replies]}}
    pages = {"channels": {"items": [{"id": "ME"}]},
             "commentThreads": {"items": [thread("1", "ME"), thread("2", "viewer", ["ME"]), thread("3", "viewer")]},
             "videos": {"items": [{"id": "v1", "snippet": {"title": "Ep"}}]}}
    http = NS(get=lambda url, **kw: NS(status_code=200, json=lambda: pages[url.rsplit("/", 1)[1]], text=""))
    got = inbox.YouTube("tok", http).comments()
    assert [(x["id"], x["answered"], x["on"]) for x in got] == [("2", True, "Ep"), ("3", False, "Ep")]
    assert got[1]["url"].endswith("v=v1&lc=3")
