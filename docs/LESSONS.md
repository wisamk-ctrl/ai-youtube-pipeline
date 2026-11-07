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
| Pay the avatar only where the face shows | Full Avatar III render 63 credits for ~16 s of face → voice-first route (speech per chunk, Avatar IV on the two face chunks, phase `assemble`) ≈ 33; the shot plan shows the face only on `face_spans.json` |
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
| Cards were stills | Source/title/number cards were PNGs with a 5 % zoom for up to 12 s: ~30 % of W45 barely moved | ~1 s CSS intro captured frame by frame in Chromium (`Renderer.animate`), drifting hold (`card_clip`); cards capped at 5 s, then a house animation (`visuals._cap_cards`, lint) |
| Every cut was a hard cut | Sections ran into each other with no breath | 12-frame dissolve only at `[Section]` boundaries (`edit.compose(sections=…)`); outgoing segment extended so the length stays frame-exact |
| Repair splices were audible | Cuts on Whisper word starts, 10 ms fades, digital-silence padding, loudness from `mean_volume` over pauses | `repair.apply`: cut at the quietest point ±120 ms around the gap's middle, 25 ms crossfades with exact length, room tone from the render's quietest pause, active-speech level matching (`speech_db`); tests on synthetic audio |

## 5. CI, GitHub and process
| Lesson | Detail |
|---|---|
| A green-looking commit can hide a red test | A commit gate checked `tail`'s exit code, not pytest's → check pytest's own code before committing |
| Pin what breaks | PyAV 19 broke faster-whisper → `av>=15,<19` with a test |
| Limits | Issue bodies over 65k chars are rejected → truncate; preview files over 100 MB rejected → bitrate sized to duration |
| Pushes race | The radar's state commit lost to a concurrent push → rebase + retry, never block the artifact |
| Artifacts | Named `week-<week>`; kept 90 days (the public-repo maximum, was 30); anyone can download them while the repo is public |
| Cancel stale runs before acting on their output | Repair phrase keys depend on the code version; clips were made only after a run on current code |
| Parallel agents in one checkout | Unfinished work goes to a `wip/` branch, never main (main is what the weekly run uses); review + full tests before main |
| This session's sandbox | Cannot download artifacts or HeyGen CDN files → previews come through the `previews` branch |
| Billing | GitHub Actions minutes ran out on a private repo → repo made public (founder: stays public for now) |
| Two runs for one week race (review #13) | The later upload of `week-<week>` wins → `concurrency:` per week in `weekly.yml` (queue, never cancel); one group for all `preview` runs (they force-push one branch) |
| A stray script run can shadow a rendered week | The render job takes the *newest* `week-<week>`; a script run's video-less upload would win → the script job refuses when the newest artifact holds `talking_head.mp4`, unless `force: true` |
| A failed render must not lose its work | Nothing was uploaded on failure → `partial-week-<week>` artifact on `failure()`; the finders ask the API for the exact name `week-<week>`, so it is never taken for the week |
| A post re-run paid Whisper twice | `transcribe_words()` caches in `output/<week>/heard.json`, keyed by the video's sha256 + model + language; repair and `run_post` share it (`tests/test_transcript_cache.py`). CI also caches `~/.cache/huggingface` (key on `WHISPER_MODEL`), `~/.cache/ms-playwright` and pip |
| Unpinned dependencies drift between runs | `requirements.txt` stays the human-edited source; CI installs `requirements.lock` (pip-compile, Python 3.12); how to refresh it is in both files' headers; a test checks every requirement is pinned |
| A red run said only "failed" | `run_pipeline.py` writes the exception or exit message to `output/<week>/error.txt`; the failed job's last step adds the log's last 40 lines; the run-failed issue quotes both, a render failure also comments on the review issue; each job type closes only its own run-failed issues |
| Comment text reached the shell | `radar-decide.yml` eval'd the comment's flags and spliced outputs into shell/JS → `scripts/radar_comment.py` parses with shlex from env, writes `GITHUB_OUTPUT` heredocs with random delimiters; later steps read env only |
| A cut issue body hid everything after it | Slicing at 64k could end inside `<details>` or a code fence (and the review issue's slice applied only to its last part) → `.github/scripts/clip.js` closes both and notes the cut |

## Founder decisions (keep in force)
- Jordanian colloquial (urban Ammani) narration — 2026-10-25.
- Premium explainer look; tech/AI animation; face only at the open and sign-off; no corner circle — 2026-10-26, 2026-11-07.
- Every claim traced to a source; never prescribe investments; never invent figures; no third-party video clips.
- Audience: enterprise leaders + a broad audience + IT people/techies — 2026-11-07.
- Voice-first render: go ahead (test passed on cost) — 2026-11-07.
- "Do all" on the enhancement list (voice-first route, upload package, Shorts, CI hardening, animated cards, smoother splices, English version, new recording guide) — 2026-11-07.
- Repo stays public for now — 2026-11-07.
- Music only if not licensed: we generate our own — 2026-11-07.

## 6. 2026-11-07 W45 repair runs
| Lesson | Detail |
|---|---|
| Repair spans depend on the code | A timing change (spoken-word counting, anchors) re-widened 3 spans, so their clip keys no longer matched: 21 of 24 instead of 24. After any change to captions/anchors, read the run's "Speech repairs" list and make the ⏳ clips in one batch call (1 credit) |
| The final edit took 53 min | Animated cards (~13 s each) and the dissolve encode add ~20 min over the 30-min edit; the transcript cache makes the next re-run skip Whisper |
| A successful run can still be wrong | The first full new-look W45 edit came out 6:21 instead of ~9:20 — programme cut at ~6:01, end card after it — and every step reported success. Now each stage's length is logged and checked against the talking head (`_check_length` in `run_pipeline.py`); a short stage fails the run and names itself; each short segment is logged. Cause confirmed by elimination: with section dissolves off (`visuals.dissolve_frames: 0`) the same edit came out full length (9:19). The xfade join in `edit.compose` loses time on the real episode though it passes on synthetic clips — keep it off until it is fixed and tested on a real week |
| Always watch the preview's length before sending it | 381 s vs the 542 s of the previous preview was the only signal |
