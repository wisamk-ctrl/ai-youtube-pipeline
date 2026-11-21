"""Mac relay for pipeline alerts (scripts/mac_alert_relay.py). Founder 2026-11-21: reuse the WhatsApp bridge that already
sends the Mac-health, NAS and bill messages. GitHub cannot reach the Mac, so the Mac polls GitHub and sends."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("relay", Path(__file__).parents[1] / "scripts" / "mac_alert_relay.py")
relay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(relay)

OWNER = "wisamk-ctrl"


def issue(n, title, login="github-actions[bot]", created="2026-11-21T06:00:00Z"):
    return {"id": 1000 + n, "number": n, "title": title, "user": {"login": login}, "created_at": created,
            "html_url": f"https://github.com/x/y/issues/{n}"}


def comment(cid, n, body, login="github-actions[bot]", created="2026-11-21T06:05:00Z"):
    return {"id": cid, "body": body, "user": {"login": login}, "created_at": created,
            "issue_url": f"https://api.github.com/repos/x/y/issues/{n}", "html_url": f"https://github.com/x/y/issues/{n}#c{cid}"}


def test_urgent_and_info_alerts_are_classified():
    titles = {52: "Review: W47"}
    assert relay.classify_issue(issue(60, "Security: channel changed"), OWNER)[0] == "urgent"
    assert relay.classify_issue(issue(61, "Show at risk"), OWNER)[0] == "urgent"
    assert relay.classify_issue(issue(62, "Run failed: render job (assemble)"), OWNER)[0] == "urgent"
    assert relay.classify_issue(issue(63, "Weekly numbers 2026-11-23"), OWNER) is None
    level, text = relay.classify_comment(comment(1, 52, "**Episode ready to check: `2026-W47-en`**\n\nlinks"), titles, OWNER)
    assert level == "info" and "2026-W47-en" in text and "publish" in text
    level, text = relay.classify_comment(comment(2, 40, "**Ready to check: `2026-11-21-brk-x-en`**"), {}, OWNER)
    assert level == "info" and "2026-11-21-brk-x-en" in text
    assert relay.classify_comment(comment(3, 52, "approve", login=OWNER), titles, OWNER) is None


def test_strangers_are_never_relayed():
    """The repo is public: anyone can open an issue or comment. Only the founder and the pipeline's bot count."""
    assert relay.classify_issue(issue(70, "Security: channel changed", login="random-user"), OWNER) is None
    assert relay.classify_comment(comment(4, 52, "**Episode ready to check: `x`**", login="random-user"), {}, OWNER) is None


def test_first_run_is_silent_then_each_alert_goes_once(tmp_path):
    state = tmp_path / "state.json"
    sent, alarms = [], []
    gh = lambda path: [issue(60, "Security: channel changed")] if "/issues?" in path else []
    relay.run(gh, sent.append, alarms.append, state, OWNER, now="2026-11-21T06:10:00Z")
    assert sent == [] and alarms == []                      # first run: remember now, send nothing old
    relay.run(gh, lambda t: sent.append(t) or True, alarms.append, state, OWNER, now="2026-11-21T06:20:00Z",
              since_override="2026-11-21T05:00:00Z")
    relay.run(gh, lambda t: sent.append(t) or True, alarms.append, state, OWNER, now="2026-11-21T06:30:00Z",
              since_override="2026-11-21T05:00:00Z")
    assert len(sent) == 1 and len(alarms) == 1 and "Security" in sent[0]


def test_a_failed_send_is_retried_next_run(tmp_path):
    state = tmp_path / "state.json"
    gh = lambda path: [comment(9, 40, "**Ready to check: `brk-a`**")] if "/comments?" in path else []
    relay.run(gh, lambda t: True, lambda t: None, state, OWNER, now="2026-11-21T06:00:00Z")   # first run
    tries = []
    relay.run(gh, lambda t: tries.append(t) and False, lambda t: None, state, OWNER, now="2026-11-21T06:10:00Z",
              since_override="2026-11-21T05:00:00Z")
    relay.run(gh, lambda t: tries.append(t) or True, lambda t: None, state, OWNER, now="2026-11-21T06:20:00Z",
              since_override="2026-11-21T05:00:00Z")
    assert len(tries) == 2
