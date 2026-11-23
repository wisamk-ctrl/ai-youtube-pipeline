"""The daily health check (pipeline/publish/health.py): a silent failure must never look like a quiet day."""
from datetime import datetime, timezone
from pathlib import Path

import yaml

from pipeline.publish import health

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 11, 23, 6, 0, tzinfo=timezone.utc)


def entry(due="2026-11-22T10:00:00Z", approved=True, **posts):
    return {"id": "2026-W47-en#1", "due": due, "approved": approved, "posts": posts}


# --- the queue -----------------------------------------------------------------------------------------------
def test_queue_clean_when_posted_or_deliberately_held():
    q = [entry(youtube={"status": "posted"}, instagram={"status": "skipped", "note": "held 2026-11-22"})]
    assert health.queue_problems(q, NOW) == []


def test_queue_flags_failed_and_unconfirmed():
    q = [entry(youtube={"status": "failed", "error": "HTTP 500"}, tiktok={"status": "unconfirmed", "error": "no answer"})]
    out = health.queue_problems(q, NOW)
    assert len(out) == 2 and "HTTP 500" in out[0] and "2026-W47-en#1" in out[0] and "by hand" in out[1]


def test_queue_flags_a_post_given_up_after_its_retries():
    q = [entry(facebook={"status": "skipped", "error": "(#200) permission", "attempts": 3})]
    assert "gave up" in health.queue_problems(q, NOW)[0]


def test_queue_flags_an_approved_due_post_nobody_sent():
    q = [entry(due="2026-11-23T01:00:00Z", youtube={"status": "queued"})]
    assert "still waiting" in health.queue_problems(q, NOW)[0]


def test_queue_ignores_not_due_unapproved_and_old():
    q = [entry(due="2026-11-23T05:30:00Z", youtube={"status": "queued"}),          # due 30 min ago: the hourly job has time
         entry(due="2026-11-29T13:00:00Z", youtube={"status": "queued"}),
         entry(approved=False, youtube={"status": "queued"}),
         entry(due="2026-10-01T10:00:00Z", youtube={"status": "failed", "error": "old"})]
    assert health.queue_problems(q, NOW) == []


# --- the news watch ------------------------------------------------------------------------------------------
def test_ingest_fresh_and_finding_items_is_fine():
    runs = [{"at": "2026-11-23T02:41+00:00", "found": 400}, {"at": "2026-11-23T04:41+00:00", "found": 420}]
    assert health.ingest_problems(runs, NOW) == []


def test_ingest_flags_a_stale_watch_and_no_runs():
    assert "2026-11-22T18:42" in health.ingest_problems([{"at": "2026-11-22T18:42+00:00", "found": 400}], NOW)[0]
    assert health.ingest_problems([], NOW)


def test_ingest_flags_runs_that_find_nothing():
    runs = [{"at": f"2026-11-23T0{h}:41+00:00", "found": 0} for h in (1, 3, 5)]
    assert "found nothing" in health.ingest_problems(runs, NOW)[0]


# --- scheduled workflows -------------------------------------------------------------------------------------
def test_workflow_flags_no_recent_success():
    last = {"social": "2026-11-23T05:23:00Z", "news-watch": "2026-11-22T10:00:00Z", "inbox": None}
    out = health.workflow_problems(last, NOW, {"social": 6, "news-watch": 8, "inbox": 50})
    assert len(out) == 2 and "news-watch" in out[0] and "inbox" in out[1] and "never" in out[1]


def test_every_scheduled_workflow_has_a_limit_in_settings():
    limits = yaml.safe_load((ROOT / "config" / "settings.yaml").read_text(encoding="utf-8"))["health"]["max_age_hours"]
    scheduled = health.scheduled_workflows(ROOT / ".github" / "workflows")
    assert set(scheduled) - {"health"} == set(limits), "a workflow with a schedule needs health.max_age_hours.<name>"


def test_every_workflow_is_watched_one_way_or_the_other():
    """Scheduled workflows: the daily last-success check. The rest: health.yml's workflow_run list, a copy of their
    names that this keeps from drifting."""
    flows = ROOT / ".github" / "workflows"
    names = {yaml.safe_load(f.read_text(encoding="utf-8"))["name"] for f in flows.glob("*.yml")}
    doc = yaml.safe_load((flows / "health.yml").read_text(encoding="utf-8"))
    watched = set(doc[True]["workflow_run"]["workflows"])                       # PyYAML reads the key `on` as True
    assert watched == names - set(health.scheduled_workflows(flows))


# --- connections ---------------------------------------------------------------------------------------------
REPORT = """**Connected accounts**

- LinkedIn: connected as **Some Name**
- Instagram: not connected (no `INSTAGRAM_TOKEN` secret)
- Composio, Facebook: Page **AI This Week**
- Composio, Instagram: connected as **@aithisweek**
- YouTube: connected to **AI This Week** (@aithisweekme) · analytics allowed
- TikTok: sign-in saved
"""


def test_identities_are_the_bold_names_per_line():
    ids = health.identities(REPORT)
    assert ids["Composio, Instagram"] == ["@aithisweek"] and ids["LinkedIn"] == ["Some Name"]
    assert "Instagram" not in ids and "TikTok" not in ids


def test_connections_clean_against_their_own_baseline():
    assert health.connection_problems(REPORT, health.identities(REPORT)) == []
    assert health.connection_problems(REPORT, {}) == []                         # first run: nothing to compare yet


def test_connections_flag_a_refused_sign_in():
    bad = REPORT.replace("connected as **Some Name**", "the saved token was refused (HTTP 401). Make a new one.")
    out = health.connection_problems(bad, health.identities(REPORT))
    assert len(out) == 1 and "LinkedIn" in out[0] and "401" in out[0]


def test_connections_flag_not_usable_and_wrong_channel():
    bad = REPORT.replace("connected as **@aithisweek**", "not usable (HTTP 403 [812])").replace(
        "· analytics allowed", "⚠️ NOT the show's channel: connect again and pick AI This Week")
    out = health.connection_problems(bad, {})
    assert len(out) == 2 and "Composio, Instagram" in out[0] and "YouTube" in out[1]


def test_connections_flag_a_changed_account():
    out = health.connection_problems(REPORT.replace("@aithisweek**", "@someone_else**"), health.identities(REPORT))
    assert len(out) == 1 and "@aithisweek" in out[0] and "@someone_else" in out[0]


def test_connections_flag_an_account_that_went_missing():
    gone = REPORT.replace("- LinkedIn: connected as **Some Name**", "- LinkedIn: not connected (no `LINKEDIN_TOKEN` secret)")
    out = health.connection_problems(gone, health.identities(REPORT))
    assert len(out) == 1 and "LinkedIn" in out[0] and "was Some Name" in out[0]


# --- the report ----------------------------------------------------------------------------------------------
def test_report_groups_problems_and_says_all_clear():
    assert "All clear" in health.report({})
    body = health.report({"Posting queue": ["a", "b"], "News watch": []})
    assert "### Posting queue" in body and "- a" in body and "News watch" not in body


def test_wallet_flags_a_low_or_unreadable_balance():
    assert health.wallet_problems(12.0, 5) == []
    assert "$1.28" in health.wallet_problems(1.28, 5)[0] and "$5" in health.wallet_problems(1.28, 5)[0]
    assert "could not be read" in health.wallet_problems(None, 5)[0]
