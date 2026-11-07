"""CI and run machinery: the workflow invariants from the 2026-11-07 engineering review."""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
WF = ROOT / ".github" / "workflows"
sys.path.insert(0, str(ROOT / "scripts"))


def _wf(name):
    return yaml.safe_load((WF / name).read_text(encoding="utf-8"))


def test_every_workflow_parses():
    for f in WF.glob("*.yml"):
        assert isinstance(yaml.safe_load(f.read_text(encoding="utf-8")), dict), f


def test_weekly_runs_one_at_a_time_per_week_and_never_cancels():
    c = _wf("weekly.yml")["concurrency"]
    assert "inputs.week" in c["group"] and "scheduled" in c["group"]
    assert c["cancel-in-progress"] is False
    assert _wf("preview.yml")["concurrency"]["cancel-in-progress"] is False


def test_week_artifacts_kept_90_days_and_partial_work_uploaded_apart():
    text = (WF / "weekly.yml").read_text(encoding="utf-8")
    assert "retention-days: 30" not in text
    steps = _wf("weekly.yml")["jobs"]["render"]["steps"]
    partial = [s for s in steps if s.get("with", {}).get("name", "").startswith("partial-week-")]
    assert partial and partial[0]["if"] == "failure()"
    # The finder asks the API for the exact name, so partial-week-* is never taken for the week.
    assert "const name = `week-${{ inputs.week }}`" in text and "listArtifactsForRepo" in text


def test_script_run_refuses_to_shadow_a_rendered_week():
    wf = _wf("weekly.yml")
    assert wf[True]["workflow_dispatch"]["inputs"]["force"]["type"] == "boolean"
    guard = [s for s in wf["jobs"]["script"]["steps"] if s.get("name") == "Refuse to shadow a rendered week"]
    assert guard and "!inputs.force" in guard[0]["if"] and "talking_head" in guard[0]["run"]


def test_workflows_install_from_the_lock():
    for f in WF.glob("*.yml"):
        assert "pip install -r requirements.txt" not in f.read_text(encoding="utf-8"), f
    lock = (ROOT / "requirements.lock").read_text(encoding="utf-8")
    pins = dict(re.findall(r"^([A-Za-z0-9_.\-]+)==(\S+)", lock, re.M))
    for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([A-Za-z0-9_.\-]+)", line.strip())
        if m and not line.strip().startswith("#"):
            name = m.group(1).lower().replace("_", "-")
            assert name in {k.lower().replace("_", "-") for k in pins}, f"{name} missing from requirements.lock"


def test_caches_for_whisper_and_chromium():
    uses = [s for s in _wf("weekly.yml")["jobs"]["render"]["steps"] if s.get("uses", "").startswith("actions/cache")]
    paths = {s["with"]["path"] for s in uses}
    assert {"~/.cache/huggingface", "~/.cache/ms-playwright"} <= paths
    assert any("WHISPER_MODEL" in s["with"]["key"] for s in uses)


def test_failures_carry_the_error_and_close_per_job_type():
    wf = _wf("weekly.yml")
    for job in ("script", "render"):
        assert wf["jobs"][job]["outputs"]["error"] == "${{ steps.fail.outputs.error }}"
        fail = [s for s in wf["jobs"][job]["steps"] if s.get("id") == "fail"][0]
        assert fail["if"] == "failure()" and "error.txt" in fail["run"] and "openssl rand" in fail["run"]
        close = [s for s in wf["jobs"][job]["steps"] if str(s.get("name", "")).startswith("Close run-failed")][0]
        assert f"Run failed: {job} job" in close["with"]["script"]
    alert = wf["jobs"]["alert"]["steps"][-1]
    assert "needs.render.outputs.error" in alert["env"]["RENDER_ERROR"]
    assert "script-review" in alert["with"]["script"]           # render failures reach the review issue
    assert "outputs.error }}" not in alert["with"]["script"]     # never spliced into the JS


def test_radar_decide_has_no_eval_and_no_spliced_outputs():
    text = (WF / "radar-decide.yml").read_text(encoding="utf-8")
    assert "eval " not in text
    for step in _wf("radar-decide.yml")["jobs"]["decide"]["steps"]:
        body = step.get("run", "") + step.get("with", {}).get("script", "")
        assert "steps.apply.outputs" not in body, step.get("name")


def test_radar_comment_parsing():
    import radar_comment as rc
    kind, name, flags = rc.parse("/promote Reflection AI --track models --group us --ar ريفلكشن --alias Beam\nthanks")
    assert (kind, name) == ("promote", "Reflection AI")
    assert flags == ["--track", "models", "--group", "us", "--ar", "ريفلكشن", "--alias", "Beam"]
    assert rc.parse("/ignore Some Startup") == ("ignore", "Some Startup", [])
    # Shell syntax stays text: no command runs, it is one argument value.
    assert rc.parse("/promote X --track models --group us --ar $(touch pwned)")[2][-2:] == ["$(touch", "pwned)"]
    for bad in ("/promote X --track models --evil 1", "/promote X --ar 'open", "hello", "/ignore  "):
        with pytest.raises(ValueError):
            rc.parse(bad)
    assert rc.branch_for("Reflection AI!") == "watchlist/reflection-ai"


def test_radar_comment_outputs_use_heredocs(tmp_path):
    import radar_comment as rc
    out = tmp_path / "out"
    rc.write_outputs(str(out), {"name": "A\nkind=evil", "result": "line1\nline2"})
    text = out.read_text(encoding="utf-8")
    assert re.search(r"^name<<EOF_[0-9a-f]{24}$", text, re.M)
    assert "\nkind=evil\n" in text            # inside the heredoc, so only data
    assert text.count("<<EOF_") == 2


def test_run_pipeline_writes_error_txt(tmp_path):
    import run_pipeline
    try:
        raise RuntimeError("HeyGen said no")
    except RuntimeError as e:
        p = run_pipeline.write_error(tmp_path, e)
    assert "RuntimeError: HeyGen said no" in p.read_text(encoding="utf-8") and "Traceback" in p.read_text(encoding="utf-8")
    p = run_pipeline.write_error(tmp_path, SystemExit("phase video: 2 unsourced claims"))
    assert p.read_text(encoding="utf-8").strip() == "phase video: 2 unsourced claims"
    assert run_pipeline.write_error(None, RuntimeError()) is None


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_clip_never_leaves_details_or_fence_open():
    clip = ROOT / ".github" / "scripts" / "clip.js"
    body = "head\n<details><summary>s</summary>\n\n```\n" + "سطر طويل\n" * 20000 + "```\n</details>\ntail"
    js = f"const c=require({json.dumps(str(clip))});const b=require('fs').readFileSync(0,'utf8');" \
         "const r=c(b);process.stdout.write(JSON.stringify({r, short: c('short')}))"
    res = json.loads(subprocess.run(["node", "-e", js], input=body, capture_output=True, text=True,
                                    check=True, env={**os.environ}).stdout)
    r = res["r"]
    assert len(r) <= 64000 and res["short"] == "short"
    assert len(re.findall(r"^```", r, re.M)) % 2 == 0
    assert r.count("<details") == r.count("</details>")
    assert r.rstrip().endswith("artifact._")
