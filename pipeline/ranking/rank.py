"""Story ranking for the weekly episode and the Shorts (docs/plans/2026-11-22-news-ranking.md, founder 2026-11-22).

    cluster (cluster.py) → judge 0-3 per criterion (judge.py) → HERE: weights, gates, slots, Shorts, decisions

Everything in this file is arithmetic and rules, with no model call, so the same judgement always gives the
same list and a founder decision re-slots the week without a new model run.

The week's ranking lives in data/ranking/<week>.json (committed, so the approval workflow can read and change
it). Each story is one addressable unit: its id, its articles, its scores and reasons, its gates, its slot.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.config import ROOT
from pipeline.models import NewsItem
from pipeline.ranking.judge import FALLBACK, KILL_TEXT, judge, story_text

DIR = ROOT / "data" / "ranking"
CRITERIA = ("decision_impact", "regional_consequence", "evidence", "tension")
SLOTS = ("deep", "quick", "radar")
ACTIONS = (*SLOTS, "short", "drop", "auto")
DEFAULTS: dict[str, Any] = {
    "enabled": True, "require_approval": True, "model": "claude-haiku-5-5",
    "max_stories": 20, "items_per_story": 5,
    "weights": {"decision_impact": 3, "regional_consequence": 2, "evidence": 1, "tension": 1},
    "deep": {"default": 3, "min": 2, "max": 4, "min_total": 11, "flex_total": 18, "seconds": [60, 180]},
    "quick": 3, "quick_seconds": [30, 45], "radar": 3,
    "shorts": {"max": 3, "breaking_hours": 48},
}


def opts(cfg: dict[str, Any]) -> dict[str, Any]:
    o = {**DEFAULTS, **(cfg.get("ranking") or {})}
    for k in ("weights", "deep", "shorts"):
        o[k] = {**DEFAULTS[k], **(o.get(k) or {})}
    return o


# ── Scores and gates ─────────────────────────────────────────────────────────
def _numbers(text: str) -> set[str]:
    return {n.replace(",", "").rstrip(".") for n in re.findall(r"\d[\d,.]*", text or "")}


def _invented_numbers(text: str, source: str) -> set[str]:
    return _numbers(text) - _numbers(source)


def score(stories: list[dict[str, Any]], judgements: dict[str, dict], cfg: dict[str, Any]) -> None:
    """Write scores, the weighted total and the four gates onto each story. The only place a total is computed."""
    o = opts(cfg)
    w = o["weights"]
    for s in stories:
        j = judgements[s["id"]]
        text = story_text(s).lower()
        scores = {c: {"score": max(0, min(3, int(j[c]["score"]))), "reason": str(j[c]["reason"]).strip()} for c in CRITERIA}
        actor = str(j.get("regional_actor") or "").strip()
        # The named-actor test: a regional consequence of 2 or 3 needs a name the sources actually carry.
        if scores["regional_consequence"]["score"] >= 2 and not (actor and actor.lower() in text):
            scores["regional_consequence"] = {"score": 1, "reason": scores["regional_consequence"]["reason"]
                                              + " (capped at 1: no named regional actor found in the sources)"}
        kind = j.get("kind") if j.get("kind") in ("global", "regional", "explainer") else "global"
        kill = j.get("kill") if j.get("kill") in KILL_TEXT else "none"
        # A global headline with no regional consequence is on the kill list. Only a model judgement can say
        # so: the keyword fallback finding no regional word is not evidence that there is no consequence.
        if kind == "global" and scores["regional_consequence"]["score"] == 0 and j.get("judged_by") != FALLBACK:
            kill = "global_no_regional"
        if s.get("advice_bait"):
            kill = "investment_call"
        depth = bool(j.get("depth")) and not s.get("routine_release")
        new = not s.get("repeat") or bool(j.get("new_development"))
        s.update({
            "kind": kind, "scores": scores, "regional_actor": actor if actor.lower() in text else "",
            "decision_frame": j.get("decision_frame") or "none", "short": j.get("short") or None,
            "judged_by": j.get("judged_by") or s.get("judged_by") or "model",
            "total": sum(w[c] * scores[c]["score"] for c in CRITERIA),
            "max_total": 3 * sum(w[c] for c in CRITERIA),
            "gates": {
                "new": {"pass": new, "reason": "new this week" if not s.get("repeat") else
                        ("new development on a story we covered: " if new else "no new development since we covered: ")
                        + "; ".join(s["repeat"])},
                "verified": {"pass": bool(s.get("verified")), "reason":
                             f"tier {'/'.join(s.get('tiers', [])) or '?'} ({', '.join(s.get('outlets', [])[:4])})"
                             if s.get("verified") else "no tier A or B outlet carries it"},
                "depth": {"pass": depth, "reason": "enough for 60-180 s" if depth
                          else "a routine version release" if s.get("routine_release")
                          else "only an announcement: not enough for 60-180 s"},
                "kill": {"pass": kill == "none", "reason": "not on the kill list" if kill == "none"
                         else f"kill list: {KILL_TEXT[kill]}"},
            },
        })


def _passes(s: dict[str, Any]) -> bool:
    return all(g["pass"] for g in s["gates"].values())


def _episode_ok(s: dict[str, Any]) -> bool:
    return _passes(s) and s["kind"] != "explainer"


def _failed(s: dict[str, Any]) -> str:
    return "; ".join(g["reason"] for g in s["gates"].values() if not g["pass"])


def _order(stories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank order. A story that fails a gate never outranks one that passes; novelty only breaks ties."""
    newest_first = sorted(sorted(stories, key=lambda s: s["id"]), key=lambda s: s["published"], reverse=True)
    return sorted(newest_first, key=lambda s: (not _episode_ok(s), -s["total"]))


def _forced(r: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for o in r.get("overrides", []):
        out[o["story_id"]] = o["action"]
    return {k: v for k, v in out.items() if v != "auto"}


# ── Slots ────────────────────────────────────────────────────────────────────
def assign_slots(r: dict[str, Any], cfg: dict[str, Any], now: datetime | None = None) -> None:
    """3 deep (flex 2-4; at least one global shift with a regional consequence and one regional-first), 3 quick,
    3 radar, the Africa and Türkiye seats, then the founder's decisions; then the Shorts and the hook."""
    o = opts(cfg)
    d = o["deep"]
    forced = _forced(r)
    for s in r["stories"]:
        s.pop("seat", None)
    order = _order(r["stories"])
    free =[s for s in order if s["id"] not in forced]
    lists: dict[str, list[dict]] = {k: [] for k in SLOTS}

    deep_pool = [s for s in free if _episode_ok(s) and s["total"] >= d["min_total"]]
    for kind in ("global", "regional"):
        pick = next((s for s in deep_pool if s["kind"] == kind), None)
        if pick:
            lists["deep"].append(pick)
    for s in deep_pool:
        if s not in lists["deep"] and (len(lists["deep"]) < d["default"]
                                       or (len(lists["deep"]) < d["max"] and s["total"] >= d["flex_total"])):
            lists["deep"].append(s)
    rest = [s for s in free if s not in lists["deep"]]
    lists["quick"] = [s for s in rest if _episode_ok(s)][:o["quick"]]
    # Gated-out stories can still be radar, except a repeat with nothing new and a generic explainer (Shorts).
    radar_ok = lambda s: (s["gates"]["new"]["pass"] and s["kind"] != "explainer"
                          and not s.get("advice_bait") and not s.get("routine_release"))
    lists["radar"] = [s for s in rest if s not in lists["quick"] and radar_ok(s)][:o["radar"]]

    for region, n in (cfg.get("scoring", {}).get("min_per_region") or {}).items():
        seated = [s for k in SLOTS for s in lists[k]]
        if sum(1 for s in seated if region in s.get("regions", [])) >= int(n):
            continue
        cand = next((s for s in free if region in s.get("regions", []) and s not in seated and radar_ok(s)), None)
        if not cand:
            continue
        cand["seat"] = region
        if _episode_ok(cand):
            lists["quick"].append(cand)
        else:
            lists["radar"].append(cand)

    by_id = {s["id"]: s for s in r["stories"]}
    for sid, action in forced.items():
        if sid in by_id and action in SLOTS:
            lists[action].append(by_id[sid])

    # Over capacity: the lowest-ranked story that nobody forced or seated moves down one slot.
    rank_of = {s["id"]: n for n, s in enumerate(order)}
    caps = {"deep": d["max"], "quick": o["quick"], "radar": o["radar"]}
    for k, nxt in (("deep", "quick"), ("quick", "radar"), ("radar", None)):
        lists[k].sort(key=lambda s: rank_of[s["id"]])
        while len(lists[k]) > caps[k]:
            movable = [s for s in lists[k] if s["id"] not in forced and not s.get("seat")] or \
                      [s for s in lists[k] if s["id"] not in forced]
            if not movable:
                break
            victim = movable[-1]
            lists[k].remove(victim)
            if nxt:         # a story that fails a gate skips the quick slot and can only be radar
                lists[nxt if nxt != "quick" or _episode_ok(victim) else "radar"].insert(0, victim)
        lists[k].sort(key=lambda s: rank_of[s["id"]])

    position = 0
    for s in r["stories"]:
        s.pop("position", None)
        s["override"] = forced.get(s["id"], "")
        s["slot"] = "out"
        s["slot_reason"] = ("dropped by the founder" if s["override"] == "drop"
                            else "generic explainer: Shorts, not the episode" if s["kind"] == "explainer"
                            else _failed(s) or "ranked below this week's slots")
    for k in SLOTS:
        for s in lists[k]:
            position += 1
            s["slot"], s["position"] = k, position
            s["slot_reason"] = ("founder decision" if s["override"] == k else
                                f"{s['seat']} seat" if s.get("seat") else
                                (_failed(s) if k == "radar" and not _passes(s) else "by rank"))
    r["hook"] = [s["id"] for s in lists["deep"] + lists["quick"]][:3]
    r["stories"] = sorted(r["stories"], key=lambda s: (s.get("position", 999), rank_of[s["id"]]))
    pick_shorts(r, cfg, now)


def pick_shorts(r: dict[str, Any], cfg: dict[str, Any], now: datetime | None = None) -> None:
    """Shorts are chosen on their own merits: one fact + one implication + one question, each from a verified
    story, with no figure the sources do not carry. Jobs: breaking context, evergreen explainer, best moment."""
    o = opts(cfg)["shorts"]
    now = now or datetime.now(timezone.utc)
    forced = _forced(r)
    cands = []
    for s in r["stories"]:
        idea = s.get("short") or {}
        want = forced.get(s["id"]) == "short"
        if forced.get(s["id"]) == "drop" or s.get("advice_bait") or not (s.get("verified") and s["gates"]["new"]["pass"]):
            continue
        if not all(str(idea.get(k) or "").strip() for k in ("fact", "implication", "question")):
            if want:        # the founder asked for it: listed, with the lines still to write
                cands.append({"story_id": s["id"], "title": s["title"], "job": "explainer", "fact": s["title"],
                              "implication": "", "question": "", "total": s["total"], "forced": True})
            continue
        if _invented_numbers(f"{idea['fact']} {idea['implication']}", story_text(s)):
            continue
        age_h = (now - datetime.fromisoformat(s["published"])).total_seconds() / 3600
        job = idea.get("job") if idea.get("job") in ("breaking", "explainer", "moment") else "explainer"
        if job == "breaking" and age_h > o["breaking_hours"]:
            job = "moment"
        if job == "moment" and s["slot"] not in ("deep", "quick"):
            job = "explainer"
        cands.append({"story_id": s["id"], "title": s["title"], "job": job, "fact": idea["fact"].strip(),
                      "implication": idea["implication"].strip(), "question": idea["question"].strip(),
                      "total": s["total"], "forced": want})
    cands.sort(key=lambda c: (not c["forced"], -c["total"]))
    chosen = [c for c in cands if c["forced"]]
    for job in ("breaking", "explainer", "moment"):          # one of each job first, then the best of the rest
        chosen += [c for c in cands if c["job"] == job and c not in chosen][:1]
    chosen += [c for c in cands if c not in chosen]
    r["shorts"] = [{k: v for k, v in c.items() if k not in ("total", "forced")} for c in chosen[:o["max"]]]
    picked = {c["story_id"] for c in r["shorts"]}
    for s in r["stories"]:
        if s["slot"] == "out" and s["id"] in picked:
            s["slot"], s["slot_reason"] = "short", "Shorts candidate, picked on its own merits"


# ── Build, decide, approve ───────────────────────────────────────────────────
def merge_same(stories: list[dict[str, Any]], judgements: dict[str, dict], items_per_story: int) -> list[dict[str, Any]]:
    """Join the stories the judge says report one event (`same_event_as`) into the first of them. The grouping by
    headline words cannot see that "Anthropic IPO" and "Anthropic's Wall Street debut" are one event (live W48
    items: four stories for it). The model only names the pair; the joining is done here. The kept story keeps
    its own judgement; a pointer to itself, to an unknown id or round a loop is ignored."""
    by_id = {s["id"]: s for s in stories}

    def root(sid: str) -> str:
        seen = {sid}
        while True:
            nxt = str((judgements.get(sid) or {}).get("same_event_as") or "")
            if not nxt or nxt not in by_id:
                return sid
            if nxt in seen:
                return ""                      # a loop: nobody is the first
            seen.add(nxt)
            sid = nxt

    roots = {s["id"]: root(s["id"]) for s in stories}      # all worked out first: joining removes judgements
    out = []
    for s in stories:
        r = roots[s["id"]]
        if r in ("", s["id"]):
            out.append(s)
            continue
        keep = by_id[r]
        keep["outlets"] = list(dict.fromkeys(keep["outlets"] + s["outlets"]))
        keep["outlet_count"] = len(keep["outlets"])
        keep["tiers"] = sorted(set(keep["tiers"]) | set(s["tiers"]))
        keep["verified"] = bool(keep.get("verified") or s.get("verified"))
        have = {i.get("source") for i in keep["items"]}
        for i in s["items"]:
            if len(keep["items"]) < items_per_story and i.get("source") not in have:
                keep["items"].append(i)
                have.add(i.get("source"))
        keep.setdefault("merged", []).append(s["title"])
        judgements.pop(s["id"], None)
    return out


def build(stories: list[dict[str, Any]], cfg: dict[str, Any], week: str, client: Any = None,
          covered: list[str] | None = None, now: datetime | None = None,
          previous: dict[str, Any] | None = None) -> dict[str, Any]:
    """Clustered stories → the week's ranking. Decisions already taken this week (`previous`) are kept."""
    now = now or datetime.now(timezone.utc)
    o = opts(cfg)
    judgements, thesis, by = judge(stories, covered or [], o["model"], client)
    stories = merge_same(stories, judgements, o["items_per_story"])
    r: dict[str, Any] = {"week": week, "generated": now.isoformat(), "judge": by, "weights": o["weights"],
                         "thesis": "", "thesis_by": "", "hook": [], "stories": stories, "shorts": [],
                         "overrides": [x for x in (previous or {}).get("overrides", [])
                                       if x["story_id"] in {s["id"] for s in stories}],
                         "approved": None}
    score(stories, judgements, cfg)
    assign_slots(r, cfg, now)
    episode = [s for s in r["stories"] if s["slot"] in SLOTS]
    sources = " ".join(story_text(s) for s in episode)
    if thesis and not _invented_numbers(thesis, sources):
        r["thesis"], r["thesis_by"] = thesis, by
    else:                                   # no model line, or one with a figure the sources do not carry
        top = [s["title"] for s in r["stories"] if s["id"] in r["hook"]]
        r["thesis"], r["thesis_by"] = ("This week: " + "; ".join(top) + ".") if top else "", "headline template"
    return r


def find(r: dict[str, Any], story_id: str) -> dict[str, Any]:
    sid = (story_id or "").strip().lower()
    for s in r["stories"]:
        if s["id"].lower() == sid:
            return s
    raise ValueError(f"no story `{story_id}` in {r['week']}; ids: {', '.join(s['id'] for s in r['stories'])}")


def decide(r: dict[str, Any], story_id: str, action: str, reason: str, by: str, cfg: dict[str, Any],
           now: datetime | None = None) -> dict[str, Any]:
    """The founder moves a story (deep, quick, radar, short), drops it, or hands it back to the ranking (auto).
    Every decision is logged with its reason, and the list has to be approved again."""
    if action not in ACTIONS:
        raise ValueError(f"unknown action `{action}`; use one of: {', '.join(ACTIONS)}")
    if not (reason or "").strip():
        raise ValueError("a decision needs a reason: /story <id> <action> because <reason>")
    s = find(r, story_id)
    now = now or datetime.now(timezone.utc)
    r.setdefault("overrides", []).append({"story_id": s["id"], "title": s["title"], "action": action,
                                          "reason": reason.strip(), "by": by, "at": now.isoformat()})
    r["approved"] = None
    assign_slots(r, cfg, now)
    return r


def approve(r: dict[str, Any], by: str, now: datetime | None = None) -> dict[str, Any]:
    r["approved"] = {"by": by, "at": (now or datetime.now(timezone.utc)).isoformat()}
    return r


def awaiting_approval(r: dict[str, Any] | None, cfg: dict[str, Any]) -> bool:
    return bool(r) and opts(cfg)["require_approval"] and not r.get("approved")


# ── Storage ──────────────────────────────────────────────────────────────────
def path(week: str) -> Path:
    base = re.match(r"\d{4}-W\d{2}", week)
    return DIR / f"{base.group(0) if base else week}.json"


def load(week: str) -> dict[str, Any] | None:
    p = path(week)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def save(r: dict[str, Any]) -> Path:
    p = path(r["week"])
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return p


# ── The review issue ─────────────────────────────────────────────────────────
def _cell(text: str, n: int = 90) -> str:
    return re.sub(r"\s+", " ", str(text)).replace("|", "/").strip()[:n]


def _clock(seconds: int) -> str:
    return f"{seconds // 60}:{seconds % 60:02d}"


def _command(s: dict[str, Any], action: str) -> str:
    return f"`/story {s['id']} {action} because …`"


def checks(r: dict[str, Any]) -> list[str]:
    """What the founder should look at before approving. Every line is computed here from the ranking."""
    out: list[str] = []
    named: set[str] = set()
    ep = [s for s in r["stories"] if s["slot"] in ("deep", "quick")]
    if r.get("judge") == FALLBACK:
        out.append("**Scores are rough.** No model judged this list (no API key, or the call failed): the scores "
                   "come from keywords and outlet tiers, so read the order as a first sort. There are no Shorts lines "
                   "and one event told under two headlines is not joined.")
    if len(ep) < 4:
        out.append(f"**Thin week:** only {len(ep)} stor{'y' if len(ep) == 1 else 'ies'} passed the gates for the "
                   "episode. Promote stories with `/story <id> deep because …` or check the outlet tiers in "
                   "config/publishers.yaml.")
    # A story left out, or only on the radar, that scored higher than one in the episode (a region seat or your
    # own decision put that one there).
    if ep:
        low = min(ep, key=lambda s: s["total"])
        beaten = sorted((s for s in r["stories"] if s["slot"] in ("out", "radar") and not s.get("override")
                         and _episode_ok(s) and s["total"] > low["total"]),
                        key=lambda s: (s["slot"] != "out", -s["total"]))
        why = f"the {low['seat']} seat" if low.get("seat") else "your decision" if low.get("override") else "its place"
        for s in beaten[:3]:
            named.add(low["id"])
            out.append(f"`{s['id']}` {_cell(s['title'], 70)} ({s['total']}/{s['max_total']}) is "
                       f"{'out' if s['slot'] == 'out' else 'only on the radar'}, and scored higher than `{low['id']}` "
                       f"({low['total']}/{low['max_total']}), which holds {why}. To bring it in: {_command(s, 'quick')}")
    # Slotted stories whose headlines mostly turn on the same word: one company twice, or one event told twice.
    slotted = [s for s in r["stories"] if s["slot"] in SLOTS]
    share: dict[str, list[str]] = {}
    for s in slotted:
        for word in s.get("common_words") or []:
            share.setdefault(word, []).append(s["id"])
    groups: dict[tuple[str, ...], list[str]] = {}
    for word, ids in sorted(share.items()):
        if len(ids) > 1:
            groups.setdefault(tuple(ids), []).append(word)
    for ids, words in groups.items():
        out.append(", ".join(f"`{i}`" for i in ids) + f" all turn on *{', '.join(words)}*: check they are not one event "
                   f"told twice. To keep one: {_command({'id': ids[-1]}, 'drop')}")
    for s in slotted:
        if s.get("seat") and s["id"] not in named:
            out.append(f"`{s['id']}` holds the {s['seat']} seat with {s['total']}/{s['max_total']}.")
        if s["slot"] == "radar" and not _passes(s):
            out.append(f"`{s['id']}` is on the radar although it fails a gate: {_failed(s)}.")
    return out


def to_md(r: dict[str, Any], cfg: dict[str, Any] | None = None) -> str:
    """The Ranking issue: what needs a decision first, then the episode in running order, then the detail."""
    o = opts(cfg or {})
    w = r.get("weights") or o["weights"]
    by_id = {s["id"]: s for s in r["stories"]}
    in_slot = {k: [s for s in r["stories"] if s["slot"] == k] for k in SLOTS}
    fallback = r.get("judge") == FALLBACK

    def link(s: dict[str, Any], n: int = 110) -> str:
        url = next((i.get("url") for i in s.get("items", []) if i.get("url")), "")
        title = _cell(s["title"], n).replace("[", "(").replace("]", ")")
        return f"[{title}]({url})" if url else title

    def entry(s: dict[str, Any]) -> list[str]:
        sc = s["scores"]
        lines = [f"{s['position']}. **{link(s)}** · `{s['id']}` · **{s['total']}/{s['max_total']}** · {s['kind']} · "
                 f"{s.get('outlet_count', 1)} outlet{'s' if s.get('outlet_count', 1) != 1 else ''} "
                 f"({'/'.join(s.get('tiers', [])) or '?'})",
                 f"   - decision {sc['decision_impact']['score']} · region {sc['regional_consequence']['score']} · "
                 f"evidence {sc['evidence']['score']} · tension {sc['tension']['score']} · in this slot: {_cell(s['slot_reason'], 120)}"]
        if s.get("judged_by") != FALLBACK:
            lines.append(f"   - why it matters: {_cell(sc['decision_impact']['reason'], 200)}")
            lines.append(f"   - in the region: {_cell(sc['regional_consequence']['reason'], 200)}"
                         + (f" (named: {s['regional_actor']})" if s.get("regional_actor") else ""))
        if s.get("merged"):
            lines.append("   - also covers: " + "; ".join(_cell(m, 80) for m in s["merged"]))
        return lines

    d, q = len(in_slot["deep"]), len(in_slot["quick"])
    low = d * o["deep"]["seconds"][0] + q * o["quick_seconds"][0]
    high = d * o["deep"]["seconds"][1] + q * o["quick_seconds"][1]
    out = [f"## Ranking {r['week']}: " + (f"approved by {r['approved']['by']}" if r.get("approved") else "waiting for your approval"),
           f"Judged by **{r['judge']}**; totals, gates and slots are computed in code.",
           f"\n**The week in one line** ({r.get('thesis_by') or 'none'}): {r.get('thesis') or '—'}",
           "**Hook teases:** " + (" · ".join(_cell(by_id[i]["title"], 70) for i in r.get("hook", []) if i in by_id) or "—"),
           "\n### Before you approve"]
    out += [f"- {c}" for c in checks(r)] or ["Nothing flagged: no story left out scored higher than one in the episode."]
    out.append(f"\n### The episode as it stands\n{d} deep, {q} quick, {len(in_slot['radar'])} radar. "
               f"The deep and quick stories run {_clock(low)} to {_clock(high)} at the configured lengths.")
    names = {"deep": f"Deep ({o['deep']['seconds'][0]}-{o['deep']['seconds'][1]} s each)",
             "quick": f"Quick ({o['quick_seconds'][0]}-{o['quick_seconds'][1]} s each)", "radar": "Radar (one line each)"}
    for k in SLOTS:
        out.append(f"\n**{names[k]}**")
        out += [line for s in in_slot[k] for line in entry(s)] or ["(none this week)"]

    out.append("\n### Shorts candidates (picked on their own merits)")
    out += [f"- **{c['job']}** · `{c['story_id']}` {_cell(c['title'], 80)}\n  - Fact: {c['fact']}\n  - Implication: {c['implication'] or '(to write)'}\n  - Question: {c['question'] or '(to write)'}"
            for c in r.get("shorts", [])] or [
        "(none: the keyword fallback does not write Shorts lines; they come with the model judge)" if fallback else
        "(none this week: no story gave one fact, one implication and one question)"]

    rest = [s for s in r["stories"] if s["slot"] in ("out", "short")]
    if rest:
        out.append(f"\n### Out of the episode ({len(rest)})")
        out += [f"- `{s['id']}` {link(s, 90)} · {s['total']}/{s['max_total']} · {_cell(s['slot_reason'], 140)}" for s in rest]

    if r.get("overrides"):
        out.append("\n### Your decisions")
        out += [f"- {x['at'][:16]} `{x['story_id']}` → **{x['action']}** by {x['by']}: {x['reason']}" for x in r["overrides"]]
    example = (rest or r["stories"] or [{"id": "<id>"}])[0]["id"]
    out.append("\n### Commands (one per comment, repository owner only)\n"
               f"- `/story {example} quick because <reason>` moves a story (or `deep`, `radar`, `short`, `drop`; "
               "`auto` hands it back to the ranking)\n"
               "- `/story approve` writes the script from this list")

    out.append("\n<details><summary>All scores</summary>\n")
    out.append(f"| id | story | slot | total | decision ×{w['decision_impact']} | region ×{w['regional_consequence']} | "
               f"evidence ×{w['evidence']} | tension ×{w['tension']} | outlets |\n|---|---|---|---|---|---|---|---|---|")
    out += [f"| {s['id']} | {_cell(s['title'], 70)} | {s['slot']} | **{s['total']}**/{s['max_total']} | "
            + " | ".join(str(s["scores"][c]["score"]) for c in CRITERIA)
            + f" | {s.get('outlet_count', 1)} ({'/'.join(s.get('tiers', []))}) |" for s in r["stories"]]
    out.append("\n</details>\n\n<details><summary>Reasons for every score and gate</summary>\n")
    for s in r["stories"]:
        out.append(f"**`{s['id']}` {_cell(s['title'], 110)}** ({s['kind']}, judged by {s['judged_by']}"
                   + (f", regional actor: {s['regional_actor']}" if s.get("regional_actor") else "") + ")")
        out += [f"- {c} {s['scores'][c]['score']}: {s['scores'][c]['reason']}" for c in CRITERIA]
        out += [f"- gate {g}: FAIL: {v['reason']}" for g, v in s["gates"].items() if not v["pass"]] or ["- all four gates pass"]
        out.append("")
    out.append("</details>")
    return "\n".join(out) + "\n"


# ── Hand-over to the script writer ───────────────────────────────────────────
def slotted_items(r: dict[str, Any]) -> list[NewsItem]:
    """The articles of the deep, quick and radar stories, in running order: all the writer may draw on."""
    seen, out = set(), []
    for s in r["stories"]:
        if s["slot"] in SLOTS:
            for d in s["items"]:
                item = NewsItem.from_dict(d)
                if item.id not in seen:
                    seen.add(item.id)
                    out.append(item)
    return out


def _ids(s: dict[str, Any]) -> list[str]:
    return [NewsItem.from_dict(d).id for d in s["items"]]


def brief(r: dict[str, Any], cfg: dict[str, Any]) -> str:
    """The approved running order, for the editorial-plan prompt."""
    o = opts(cfg)
    lo, hi = o["deep"]["seconds"]
    qlo, qhi = o["quick_seconds"]
    lines = ["The running order below was ranked and approved by the founder. Follow it exactly: do not add, drop or",
             "reorder stories; it replaces the story count and the ordering instruction above. Set each segment's",
             "story_id to the id given.",
             f"Weekly thesis (one sentence the episode keeps returning to; sharpen the wording, keep the point): {r.get('thesis') or '(write one)'}",
             "The cold open teases the first three stories.",
             f"\nDEEP stories, one segment each, {lo}-{hi} s, in this order. Each follows the same arc: the fact (attributed)",
             "→ what it means for the region → what to ask or watch next (a question for a vendor or a team; information",
             "only, never investment advice). Put that last beat in watch_next."]
    def line(s: dict[str, Any]) -> str:
        actor = f"; regional actor: {s['regional_actor']}" if s.get("regional_actor") else ""
        frame = f"; decision frame: {s['decision_frame']}" if s.get("decision_frame") not in (None, "", "none") else ""
        return f"- story_id={s['id']} «{s['title']}» item_ids={','.join(_ids(s))}{actor}{frame}"
    lines += [line(s) for s in r["stories"] if s["slot"] == "deep"] or ["(none)"]
    lines.append(f"\nQUICK stories, one short segment each, {qlo}-{qhi} s: the fact and one line on why it matters here.")
    lines += [line(s) for s in r["stories"] if s["slot"] == "quick"] or ["(none)"]
    lines.append("\nRADAR, one line each with its reason, no segment: put their item ids in quick_fire_item_ids.")
    lines += [line(s) + f" (why radar: {s['slot_reason']})" for s in r["stories"] if s["slot"] == "radar"] or ["(none)"]
    return "\n".join(lines)


def align_plan(plan: Any, r: dict[str, Any]) -> list[str]:
    """Stamp each plan segment with its story and put the segments in the approved order (in code, whatever
    order the model wrote them in). Returns the ids of deep or quick stories the plan left out."""
    running = [s for s in r["stories"] if s["slot"] in ("deep", "quick")]
    ids = {s["id"]: set(_ids(s)) for s in running}
    for seg in plan.segments:
        overlap = {sid: len(have & set(seg.item_ids)) for sid, have in ids.items()}
        best = max(overlap, key=overlap.get, default="")
        seg.story_id = best if best and overlap[best] else ""
    place = {s["id"]: n for n, s in enumerate(running)}
    plan.segments.sort(key=lambda seg: place.get(seg.story_id, len(place)))
    used = {seg.story_id for seg in plan.segments}
    return [s["id"] for s in running if s["id"] not in used]
