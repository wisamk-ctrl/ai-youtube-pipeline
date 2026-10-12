"""
Listener-side quality gate (item 2 of the professional-grade plan).

The reviewer pass checks facts and length. This pass reads the finished script the way
a viewer hears it and scores it. Anything under the bar goes back to the reviewer with
the critic's three fixes as explicit instructions, up to `critic.max_rounds` times.

Scores (1-10): hook, clarity, pacing, flow (transitions and signposts), arabic (register,
no calques, style-guide compliance), value (does each story answer "why it matters here").
Bar: every score ≥ `critic.min_score` (default 8). critique.json keeps every round.
"""

from __future__ import annotations

import logging
from typing import Any

import anthropic
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)


class Fix(BaseModel):
    where: str = Field(description="Which segment or line (quote 3-6 Arabic words)")
    problem: str = Field(description="What a listener experiences, in one sentence")
    fix: str = Field(description="The concrete rewrite instruction for the reviewer")


class Critique(BaseModel):
    hook: int = Field(ge=1, le=10, description="Do the first 20 seconds make a busy executive keep listening?")
    clarity: int = Field(ge=1, le=10, description="Is every story understood on first hearing, no re-reading needed?")
    pacing: int = Field(ge=1, le=10, description="Sentence length, pauses, nothing drags or rushes")
    flow: int = Field(ge=1, le=10, description="Signposts and transitions between segments")
    arabic: int = Field(ge=1, le=10, description="Broadcast MSA, no calques, style guide respected, names/numbers spoken right")
    value: int = Field(ge=1, le=10, description="Each story says why it matters to enterprises in the region")
    worst_three: list[Fix] = Field(min_length=1, max_length=3)
    verdict: str = Field(description="One sentence a head of news would say about this draft")

    @property
    def scores(self) -> dict[str, int]:
        return {k: getattr(self, k) for k in ("hook", "clarity", "pacing", "flow", "arabic", "value")}

    @property
    def minimum(self) -> int:
        return min(self.scores.values())


SYSTEM = """You are the head of news at a leading Arabic business channel, reviewing a script minutes before
recording. You did not write it and you owe it nothing. Read it as the audience will HEAR it: senior
executives, CTOs and founders across the Gulf and the Arab world, on a phone, often with the sound low.
Score strictly against the style guide; a 10 means you would air it unchanged. Then name the three
things that most hurt the listener, each with a concrete rewrite instruction. Praise is not useful.
The script may contain production markers in square brackets; they are not spoken.

<style_guide>
{style_guide}
</style_guide>"""


def critique(script: str, style_guide: str, model: str, client: anthropic.Anthropic) -> Critique:
    resp = client.messages.parse(
        model=model, max_tokens=4000,
        system=SYSTEM.format(style_guide=style_guide),
        messages=[{"role": "user", "content": f"Score this script.\n\n<script>\n{script}\n</script>"}],
        output_format=Critique,
    )
    if resp.stop_reason != "end_turn" or resp.parsed_output is None:
        raise RuntimeError(f"critic stopped early: {resp.stop_reason}")
    return resp.parsed_output


def fixes_as_instruction(c: Critique) -> str:
    """Turn the critic's worst-three into the reviewer's marching orders."""
    lines = [f"A listener-side review scored this draft {c.scores} — verdict: {c.verdict}",
             "Apply these three fixes exactly, keeping everything else:"]
    for n, f in enumerate(c.worst_three, 1):
        lines.append(f"{n}. At «{f.where}»: {f.problem} → {f.fix}")
    return "\n".join(lines)


def summary(rounds: list[dict[str, Any]]) -> str:
    return " | ".join(f"r{n + 1}: min {r['minimum']} ({', '.join(f'{k} {v}' for k, v in r['scores'].items())})"
                      for n, r in enumerate(rounds))
