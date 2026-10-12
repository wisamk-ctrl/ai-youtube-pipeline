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
from dataclasses import dataclass
from datetime import date
from typing import Any

import anthropic
from typing import Literal

from pydantic import BaseModel, Field

from pipeline.models import NewsItem
from pipeline.script_format import count_spoken_words
from pipeline.scripting import prompts

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
            max_tokens=32000,  # ~1k Arabic words is ~3-4k tokens; headroom for thinking
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config={"effort": self.cfg.get("effort", "high")},
            betas=[FALLBACK_BETA],
            fallbacks="default",
        ) as stream:
            message = stream.get_final_message()
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
            presenter_name=self.cfg["presenter_name"], channel_name=self.cfg["channel_name"]
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
    def review(self, draft: str, items: list[NewsItem]) -> str:
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
            draft=draft,
            items_block=_items_block(items),
        )
        return self._generate(prompts.REVIEWER_SYSTEM, user, "review pass")

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

        return ScriptResult(plan=plan, script=script, word_count=words, target_words=self.target_words)
