"""
Phase 2 — the scripting engine (Anthropic Claude prompt chain).

    filtered NewsItems
        │
        ▼  Step 1  client.messages.parse  → EditorialPlan (validated Pydantic object)
        │
        ▼  Step 2  streamed generation     → Arabic draft with pacing markers
        │
        ▼  Step 3  streamed review pass    → fact-checked, length-corrected script
        │           (repeated up to max_revisions while the length is out of tolerance)
        ▼
    ScriptResult(plan, script, word_count)

API choices (current Anthropic API, Opus 5.5):
* Model `claude-opus-5-5`. Thinking is always on for this model, so we don't
  send a `thinking` parameter; depth is controlled with `output_config.effort`
  (default for this model is "medium", we raise it to "high" for writing).
* Long outputs use streaming + `get_final_message()` so an 8-minute script
  never hits an HTTP timeout.
* The writing calls opt into server-side refusal fallbacks (`fallbacks="default"`).
  News about AI security incidents can occasionally trip a safety classifier; with
  fallbacks the API re-runs the request on Anthropic's recommended fallback model
  instead of returning an empty script.
* Every response's `stop_reason` is checked before its content is used.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import anthropic
from typing import Literal

from pydantic import BaseModel, Field

from pipeline import usage
from pipeline.config import ROOT
from pipeline.models import NewsItem
from pipeline.script_format import count_spoken_words
from pipeline.scripting import critic as critic_mod
from pipeline.scripting import prompts
from pipeline.scripting import source_map as smap_mod

log = logging.getLogger(__name__)

FALLBACK_BETA = "server-side-fallback-2026-07-01"  # header for the `fallbacks="default"` form


# ── Structured output schema for Step 1 ──────────────────────────────────────
class Segment(BaseModel):
    track: Literal["models", "agents", "chips", "radar", "other"] = Field(
        description="Beat of the episode: models (labs & LLMs), agents, chips (chips & inference), radar (new names), other")
    item_ids: list[str] = Field(description="IDs of the source items this segment is built from")
    headline_en: str = Field(description="One-line English working headline")
    angle: str = Field(description="The angle/narrative for this story, in English")
    enterprise_impact: str = Field(description="Why it matters to enterprises in the GCC/MENA, in English")
    broll_ideas: list[str] = Field(description="2-3 concrete B-roll or graphic ideas")
    approx_seconds: int = Field(description="Planned airtime in seconds")


class EditorialPlan(BaseModel):
    episode_title_ar: str = Field(description="YouTube title in Arabic, ≤70 characters, no clickbait")
    cold_open_hook_en: str = Field(description="The 15-20 second opening hook idea, in English")
    segments: list[Segment]
    quick_fire_item_ids: list[str] = Field(description="Optional minor items for a 30-second quick-fire round")
    thumbnail_text_ar: str = Field(description="2-4 Arabic words for the thumbnail")


@dataclass
class ScriptResult:
    plan: EditorialPlan
    script: str
    word_count: int
    target_words: int
    critique_rounds: list[dict[str, Any]] = field(default_factory=list)
    source_map_md: str = ""
    source_stats: dict[str, Any] = field(default_factory=dict)


class ScriptGenerationError(RuntimeError):
    pass


# ── Helpers ──────────────────────────────────────────────────────────────────
def _items_block(items: list[NewsItem]) -> str:
    """Serialise items for the prompt. IDs let the plan reference items unambiguously."""
    return "\n\n".join(
        f"<item id=\"{i.id}\" source=\"{i.source}\" published=\"{i.published.date()}\" "
        f"score=\"{i.score}\" track=\"{i.track or 'other'}\" region=\"{i.region}\" "
        f"entities=\"{', '.join(i.entities)}\">\n<title>{i.title}</title>\n<url>{i.url}</url>\n"
        f"<body>{i.summary}</body>\n</item>"
        for i in items
    )


def _check_stop(message: Any, step: str) -> None:
    """Fail loudly on anything other than a clean finish — never ship a truncated script."""
    if message.stop_reason == "refusal":
        details = getattr(message, "stop_details", None)
        raise ScriptGenerationError(f"{step}: model declined (category={getattr(details, 'category', None)})")
    if message.stop_reason == "max_tokens":
        raise ScriptGenerationError(f"{step}: output hit max_tokens — raise the limit")
    if message.stop_reason != "end_turn":
        raise ScriptGenerationError(f"{step}: unexpected stop_reason={message.stop_reason}")


def _text_of(message: Any) -> str:
    """Join text blocks only (thinking/fallback blocks are skipped)."""
    return "".join(b.text for b in message.content if b.type == "text").strip()


class ScriptEngine:
    def __init__(self, cfg: dict[str, Any], client: anthropic.Anthropic | None = None) -> None:
        self.cfg = cfg["scripting"]
        # The client reads ANTHROPIC_API_KEY from the environment; SDK retries
        # 429/5xx/connection errors twice with backoff by default — bump to 4
        # for an unattended weekly job.
        self.client = client or anthropic.Anthropic(max_retries=4)
        self.target_words = round(self.cfg["target_minutes"] * self.cfg["words_per_minute"])
        self.style_guide = (ROOT / "config" / "style_guide.md").read_text(encoding="utf-8")
        self.rubric = (ROOT / "config" / "critic_rubric.md").read_text(encoding="utf-8")

    # ── Step 1 ──
    def plan(self, items: list[NewsItem], week_label: str) -> EditorialPlan:
        response = self.client.messages.parse(
            model=self.cfg["model"],
            max_tokens=16000,
            system=prompts.EDITOR_SYSTEM,
            messages=[{
                "role": "user",
                "content": prompts.EDITOR_USER.format(
                    stories_min=self.cfg["stories_min"],
                    stories_max=self.cfg["stories_max"],
                    target_minutes=self.cfg["target_minutes"],
                    week_label=week_label,
                    items_block=_items_block(items),
                ),
            }],
            output_format=EditorialPlan,
        )
        usage.record("plan", self.cfg["model"], getattr(response, "usage", None))
        _check_stop(response, "editorial plan")
        plan = response.parsed_output

        # Guard against the model citing an ID that doesn't exist (it would
        # then write about a story we can't source).
        known = {i.id for i in items}
        for seg in plan.segments:
            unknown = set(seg.item_ids) - known
            if unknown:
                log.warning("Plan referenced unknown item IDs %s — dropping them", unknown)
                seg.item_ids = [x for x in seg.item_ids if x in known]
        plan.segments = [s for s in plan.segments if s.item_ids]
        if not plan.segments:
            raise ScriptGenerationError("editorial plan has no sourceable segments")
        log.info("Plan: %d segments — %s", len(plan.segments), plan.episode_title_ar)
        return plan

    # ── Streaming call used by Steps 2 and 3 ──
    def _generate(self, system: str, user: str, step: str) -> str:
        with self.client.beta.messages.stream(
            model=self.cfg["model"],
            max_tokens=64000,  # thinking tokens count against this; a 1k-word Arabic script is ~4k, the rest is reasoning room
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config={"effort": self.cfg.get("effort", "high")},
            betas=[FALLBACK_BETA],
            fallbacks="default",
        ) as stream:
            message = stream.get_final_message()
        usage.record(step, getattr(message, "model", self.cfg["model"]), getattr(message, "usage", None))
        _check_stop(message, step)
        if any(b.type == "fallback" for b in message.content):
            log.warning("%s: primary model declined; served by fallback model %s", step, message.model)
        text = _text_of(message)
        if not text:
            raise ScriptGenerationError(f"{step}: empty response")
        return text

    @staticmethod
    def selected_items(plan: EditorialPlan, items: list[NewsItem]) -> list[NewsItem]:
        """Only the items the plan uses: less noise, lower cost, and the writer
        and reviewer can't drift into stories the editor rejected."""
        used = {i for s in plan.segments for i in s.item_ids} | set(plan.quick_fire_item_ids)
        return [i for i in items if i.id in used]

    # ── Step 2 ──
    def write(self, plan: EditorialPlan, items: list[NewsItem]) -> str:
        selected = self.selected_items(plan, items)
        system = prompts.WRITER_SYSTEM.format(
            presenter_name=self.cfg["presenter_name"], channel_name=self.cfg["channel_name"],
            style_guide=self.style_guide,
        )
        user = prompts.WRITER_USER.format(
            target_words=self.target_words,
            target_minutes=self.cfg["target_minutes"],
            wpm=self.cfg["words_per_minute"],
            plan_json=json.dumps(plan.model_dump(), ensure_ascii=False, indent=2),
            items_block=_items_block(selected),
        )
        return self._generate(system, user, "draft script")

    # ── Step 3 ──
    def review(self, draft: str, items: list[NewsItem], extra_instructions: str = "") -> str:
        current = count_spoken_words(draft)
        tol = self.cfg["length_tolerance"]
        delta = self.target_words - current
        if abs(delta) <= self.target_words * tol:
            instruction = "Length is within tolerance — keep it roughly the same."
        elif delta > 0:
            instruction = f"Expand by about {delta} words, deepening the enterprise-impact analysis."
        else:
            instruction = f"Cut about {-delta} words, trimming the least important passages first."

        user = prompts.REVIEWER_USER.format(
            current_words=current,
            target_words=self.target_words,
            tolerance_pct=round(tol * 100),
            length_instruction=instruction,
            extra_instructions=extra_instructions,
            draft=draft,
            items_block=_items_block(items),
        )
        return self._generate(prompts.REVIEWER_SYSTEM.replace("{style_guide}", self.style_guide), user, "review pass")

    # ── Full chain ──
    def run(self, items: list[NewsItem], week_label: str | None = None) -> ScriptResult:
        week_label = week_label or date.today().isoformat()
        plan = self.plan(items, week_label)
        script = self.write(plan, items)
        log.info("Draft: %d spoken words (target %d)", count_spoken_words(script), self.target_words)

        # The review pass always runs once (fact-check + polish); it repeats
        # only while the length is still outside tolerance.
        sources = self.selected_items(plan, items)
        tol_words = self.target_words * self.cfg["length_tolerance"]
        for attempt in range(1 + self.cfg["max_revisions"]):
            script = self.review(script, sources)
            words = count_spoken_words(script)
            log.info("Review %d: %d spoken words", attempt + 1, words)
            if abs(words - self.target_words) <= tol_words:
                break
        else:
            log.warning("Script length still off target after revisions; continuing (%d words)", words)

        # Listener-side gate: score like a head of news; below the bar → the reviewer applies the
        # critic's three fixes and we score again. The last critique always stands in the record.
        ccfg = self.cfg.get("critic", {})
        rounds: list[dict[str, Any]] = []
        for attempt in range(ccfg.get("max_rounds", 2) + 1):
            c, rec = self.critique(script)
            rounds.append(rec)
            log.info("Critic round %d: min %d (samples %s) — %s", attempt + 1, c.minimum, rec["samples"], c.verdict)
            if c.minimum >= ccfg.get("min_score", 8) or attempt == ccfg.get("max_rounds", 2):
                break
            script = self.review(script, sources, extra_instructions=critic_mod.fixes_as_instruction(c))
            words = count_spoken_words(script)
        if rounds[-1]["minimum"] < ccfg.get("min_score", 8):
            log.warning("Script still below the quality bar (min %d) after %d rounds — review the critique", rounds[-1]["minimum"], len(rounds))

        source_md, source_stats = self.source_map(script, sources)
        return ScriptResult(plan=plan, script=script, word_count=words, target_words=self.target_words,
                            critique_rounds=rounds, source_map_md=source_md, source_stats=source_stats)

    def critique(self, script: str) -> tuple[critic_mod.Critique, dict[str, Any]]:
        """Double-scored, rubric-based critique; returns the consensus and its critique.json record."""
        ccfg = self.cfg.get("critic", {})
        c, samples, stable = critic_mod.consensus(script, self.style_guide, self.rubric, ccfg,
                                                  ccfg.get("model", self.cfg["model"]), self.client)
        return c, critic_mod.round_record(c, samples, stable)

    def source_map(self, script: str, sources: list[NewsItem]) -> tuple[str, dict[str, Any]]:
        """Every spoken sentence attributed to its sources; unsourced claims are listed first."""
        sents, smap = smap_mod.build(script, sources, self.cfg.get("aux_model", self.cfg["model"]), self.client)
        source_md, source_stats = smap_mod.render_md(sents, smap, sources), smap_mod.stats(smap)
        if source_stats["unsourced"]:
            log.warning("%d unsourced claim(s) in the script — see source_map.md", source_stats["unsourced"])
        return source_md, source_stats

    def score(self, plan: EditorialPlan, script: str, items: list[NewsItem],
              rounds: list[dict[str, Any]]) -> ScriptResult:
        """Critic + source map only, on a script as given (e.g. one edited by hand). No rewriting."""
        sources = self.selected_items(plan, items)
        ccfg = self.cfg.get("critic", {})
        c, rec = self.critique(script)
        rounds = rounds + [rec]
        log.info("Critic round %d: min %d (samples %s) — %s", len(rounds), c.minimum, rec["samples"], c.verdict)
        source_md, source_stats = self.source_map(script, sources)
        return ScriptResult(plan=plan, script=script, word_count=count_spoken_words(script), target_words=self.target_words,
                            critique_rounds=rounds, source_map_md=source_md, source_stats=source_stats)

    def polish(self, plan: EditorialPlan, script: str, items: list[NewsItem],
               rounds: list[dict[str, Any]]) -> ScriptResult:
        """Apply the last critique's three fixes to an existing script, score again, rebuild the source map.

        One reviewer pass + one critic round, so a below-bar script can be nudged without
        regenerating the episode. The new round is appended to the existing record.
        """
        if not rounds:
            raise ValueError("polish needs at least one critique round to apply")
        last = critic_mod.Critique(**rounds[-1]["scores"], worst_three=rounds[-1]["worst_three"], verdict=rounds[-1]["verdict"])
        sources = self.selected_items(plan, items)
        script = self.review(script, sources, extra_instructions=critic_mod.fixes_as_instruction(last))
        words = count_spoken_words(script)
        log.info("Polish: %d spoken words (target %d)", words, self.target_words)
        ccfg = self.cfg.get("critic", {})
        c, rec = self.critique(script)
        rounds = rounds + [rec]
        log.info("Critic round %d: min %d (samples %s) — %s", len(rounds), c.minimum, rec["samples"], c.verdict)
        if c.minimum < ccfg.get("min_score", 8):
            log.warning("Script still below the quality bar (min %d) — review the critique", c.minimum)
        source_md, source_stats = self.source_map(script, sources)
        return ScriptResult(plan=plan, script=script, word_count=words, target_words=self.target_words,
                            critique_rounds=rounds, source_map_md=source_md, source_stats=source_stats)
