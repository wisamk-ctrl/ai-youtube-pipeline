# Lessons learned — every run so far

What went wrong (or right) in each run, why, and where the fix now lives so it cannot happen again.
Add to this file whenever a run teaches something. Editorial lessons for the script also go into
`config/lessons_editorial.md`, which the writer, reviewer and critic read on every run.

**Before any run, check:** the founder's decisions (bottom of this file), the HeyGen cost rules in
`docs/STATUS.md`, and the HeyGen credit balance.

## 1. Script and voice
| Lesson | What happened | Now enforced by |
|---|---|---|
| The house rules can cause the fault | Style guide §3 *required* «Arabic Latin» names; the rubric penalised a missing Latin name; the voice said every name twice (W45, 11×) | Braces rule «أوبن إيه آي{OpenAI}» in style guide, rubric, writer prompt; `speakable()` drops braces |
| Check what the voice reads, not what is written | Glosses, versions, letter-digit names, jargon stacks all passed the critic, who read the written script | `lint_voice()` → `voice_lint.md`, fed to reviewer and critic |
| Hard names need a spoken form | G42 → «جي اتنان وأربعون», Claude → "cloud", HUMAIN spelled out | `config/pronunciation.yaml`, lint flags letter-digit tokens |
| Vowel marks misread, and stripping them changes meaning | «عن بُعد» → «عم بوعد»; stripped «بعد» reads "after" | No harakat; banned phrases in `config/voice.yaml` |
| Jordanian colloquial, not MSA | Founder decision 2026-10-25 | Style guide, rubric (MSA = MAJOR) |
| One story in the hook; vary «ليش بيهمّنا» | W45: three headlines in 20 s; the question 7× | Rubric, lint, `config/lessons_editorial.md` |

## 2. Sourcing and facts
| Lesson | What happened | Now enforced by |
|---|---|---|
| Our own tools are not sources | W45 said on air Tencent wasn't on the watchlist; it was ("Tencent Hunyuan" — the radar matched exact names only). "Radar" also appeared as an on-screen source | `is_known()` containment match; radar items uncitable; correction slot via `repairs.yaml` `correct:` |
| Headlines are not articles | Google News gives headline + publisher only; «حسب رويترز» was checked against a headline | `pipeline/ingestion/articles.py` fetches the article (best effort) |
| Not all publishers are equal | shattered.io weighed the same as Reuters and was shown on screen | `config/publishers.yaml` tiers; tier C never gets a source card |
| A warning nobody reads is not a check | The source map warned about unsourced claims; recording went ahead | Video/import refuse unsourced claims unless `reviewed/<week>/sources_ok.txt` |
| Check the full source the writer saw | The checker cut items at 1,500 chars, flagging real figures as unsourced every week | Checker sees the writer's full text (test pins it) |

## 3. HeyGen, avatar and costs
| Lesson | Detail |
|---|---|
| API credits ≠ plan credits | The plan's monthly credits are not API credits; API renders failed. The HeyGen connector (from chat) and the web app use plan credits |
| Measured costs (2026-11-07) | Avatar III photo, full render via connector ≈ 7 credits/min (web app ≈ 4/min). Avatar IV audio-driven ≈ 21/min. Speech ≈ 3/min, **1 credit minimum per call** |
| Batch speech | Generate every repair phrase in ONE speech call and cut it by the returned word timestamps (`url#t=a,b`): 19 phrases for 3 credits instead of 19+ |
| Lip sync is the engine, not the edit | The edit takes picture and sound from the same file frame-exactly; Avatar III photo lip sync is poor → face only at open and sign-off; voice-first render planned |
| The corner circle looked wrong | Founder rejected it 2026-11-07 → `visuals.corner.enabled: false` |
| Secrets left empty | IDs (avatar, voice) live in `config/settings.yaml`, overridable by secrets/inputs; IDs are not credentials |
| Resolving a link | A HeyGen account ID was taken for a video ID → CDN links are used as-is |

## 4. Edit, visuals and sound
| Lesson | What happened | Now enforced by |
|---|---|---|
| Never fall back to the face | A failed visual showed the face, against minimal-face mode | Fallback is the tech animation |
| Stock must match the story | Preview showed a mermaid, strawberries, a bicycle wheel; one clip three times | Tag-relevance filter, off-topic tags rejected, no clip reuse per query |
| Loudness | W45 measured −19.6 LUFS (YouTube plays it ~5 dB quiet) | Two-pass loudnorm to −14 LUFS, our generated music bed |
| Whisper merges doubled words | Cutting by Whisper word times is unreliable | Repairs replace the whole span between two cleanly heard words (runs of 2+) |
| Repairs are per render | The written script cannot tell whether a render has a fault | Repair only for weeks with `reviewed/<week>/repairs.yaml`; optional `render:` guard |
| Clip links expire | One dead link would have failed the whole edit | A bad clip leaves that phrase as rendered |
| Director output | Structured JSON was truncated; the fallback put the face on 80 % | Streaming plain text with full-answer retry; fallback fills with house stock |

## 5. CI, GitHub and process
| Lesson | Detail |
|---|---|
| A green-looking commit can hide a red test | A commit gate checked `tail`'s exit code, not pytest's → check pytest's own code before committing |
| Pin what breaks | PyAV 19 broke faster-whisper → `av>=15,<19` with a test |
| Limits | Issue bodies over 65k chars are rejected → truncate; preview files over 100 MB rejected → bitrate sized to duration |
| Pushes race | The radar's state commit lost to a concurrent push → rebase + retry, never block the artifact |
| Artifacts | Named `week-<week>`; expire after 30 days; anyone can download them while the repo is public |
| Cancel stale runs before acting on their output | Repair phrase keys depend on the code version; clips were made only after a run on current code |
| Parallel agents in one checkout | Unfinished work goes to a `wip/` branch, never main (main is what the weekly run uses); review + full tests before main |
| This session's sandbox | Cannot download artifacts or HeyGen CDN files → previews come through the `previews` branch |
| Billing | GitHub Actions minutes ran out on a private repo → repo made public (founder: stays public for now) |

## Founder decisions (keep in force)
- Jordanian colloquial (urban Ammani) narration — 2026-10-25.
- Premium explainer look; tech/AI animation; face only at the open and sign-off; no corner circle — 2026-10-26, 2026-11-07.
- Every claim traced to a source; never prescribe investments; never invent figures; no third-party video clips.
- Audience: enterprise leaders + a broad audience + IT people/techies — 2026-11-07.
- Voice-first render: go ahead (test passed on cost) — 2026-11-07.
- Repo stays public for now — 2026-11-07.
- Music only if not licensed: we generate our own — 2026-11-07.
