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

## 7. 2026-11-08 voice lab (no HeyGen credits)
| Lesson | Detail |
|---|---|
| Check each repair clip on its own before splicing | The founder heard ADNOC wrong at 0:03; the voice lab showed the HeyGen clip itself said «نوك و G42» (the «وأد» was lost from its cut), and «تشغّل كلود كود» was unintelligible. `voice-lab --clips` now transcribes every clip in use and every alternative and picks the clearer |
| The spelling «أدنوك» is right | Microsoft's Jordanian/Saudi voices, XTTS and the converted voice all say «أدنوك» correctly; «آدنوك» and «أد نوك» are worse |
| Why the clone's Arabic sounds off | Whisper large-v3-turbo on W45: versions read as MSA («اثنان نقطة واحد…»), English names mangled (Perplexity → «بربلك سيتي», SemiAnalysis → «CME Analysis»), emphatics softened («ذكاء اصطناعي» → «دكاء استناعي»). The first two are script rules (braces, no spoken versions); the third is the clone itself → re-record (docs/recording_script.md) |
| Free voice tools, scored | Microsoft ar-JO-TaimNeural: error 4 %, similarity 0.14 (not the founder). XTTS-v2: 5 %, 0.74, but non-commercial licence. kNN-VC (MIT) converting the Jordanian reading into the show voice: 7 %, 0.73 on sentences — but weak on short phrases (13 % mean, «جي» → «دي»); 16 kHz output |
| Whisper writes names in Latin letters | «G42», «NVIDIA», «Claude Code» in Latin count as errors to a character score though the pronunciation may be right; judge those by ear |

## 8. 2026-11-09 own-voice W45
| Lesson | Detail |
|---|---|
| Don't denoise a quiet room | The founder's read (phone memo, 63 kbps AAC, −71 dB noise floor) came out "muffled": afftdn took ~3 dB off 3–10 kHz on a recording that was already dark. The voice chain now has no denoise, a mud cut, presence/air lift and a de-esser (3–6 kHz +9 dB, 6–10 kHz +12 dB against the old chain) |
| Record lossless if you can | The phone memo is compressed at 63 kbps; iPhone Voice Memos → Settings → Audio Quality → Lossless (or any WAV recorder) keeps the top end |
| Stale reports | An own-voice run posted the previous avatar run's repairs list (the artifact still held repairs.md); own-voice runs now delete it |
| Phrase lists miss what the recogniser hides | The first W45 cut run listed four stumbles and cut none: CI's Whisper (medium) spelled them differently, or heard the stumble once. Now exact back-to-back repeats are cut without a list, phrases take `|` spellings and match a cut-off first saying, a stumble cut is at most 4 s, `cut:` takes time spans, and the issue report carries the timed transcript and the phrases not found |
| One bad secret stops every Claude phase | 2026-11-11: `ANTHROPIC_API_KEY` returned 401 (invalid x-api-key), so `translate` failed while the Claude-free `assemble` passed. ingest/script/polish/translate all need it: check the key before a Saturday run |
| Cut stumbles by time, from a strong recogniser | Even with spellings and back-to-back detection, CI's Whisper medium heard three of W45's four stumbles once. The `words` workflow (large-v3-turbo, no VAD) lists every word with its time; `cut:` spans read off it are exact. Run it first on every own-voice week, then set `cut:` before the assemble run |

## 9. 2026-11-12 process review: the edit follows the script
| Lesson | Detail |
|---|---|
| Compare with what was meant, not only with what was said | W45's stumbles were listed by hand over six 71-minute runs. The script is known, so `guided.py` walks the recording against it: a jump back is a retake, words repeating their neighbours between two script words are a stumble, a later file's sentence replaces the main take's. On W45's word list it found all 7 hand-found cuts, a retake nobody had heard (6:03) and a swapped name pair (8:45) |
| One recogniser, once | Two recognisers disagreed and CI's `medium` changed its mind between runs («وشركات وشركات»). The own-voice edit uses large-v3-turbo without VAD, cached per recording file; the captions reuse those words, so the edit pays for Whisper once instead of twice (~22 min → one pass) |
| Hear before you render | A wrong cut used to cost a full edit. Phase `voicecheck` makes only the cleaned read and its report; the video is made after the founder has heard it |
| Fix a sentence with a sentence | A misread no longer needs the whole take again: read the sentence into a new file, list it under `pickups:` |
| Don't cut what is not a repeat | Words not in the script (an ad-lib «طيب يعني») stay; only repeats of the words around them are cut. `keep:` protects anything cut by mistake |
| Where the 71 minutes went | Whisper ×2 22 min, final encode 15, visuals 11, cue-card overlay 10, edit 5, Shorts 4. Still open: one encode for overlay + captions + master instead of three |

## 10. 2026-11-12 first viewers' feedback (English W45)
| Lesson | Detail |
|---|---|
| Dense news needs a slower voice | The English clone read ~185 words/min; viewers asked for slower (they can speed up themselves). Generated speech is now slowed at assemble (`video.voicefirst.tempo_en: 0.88`, pitch kept, the face clip with it); the founder's own read is never touched |
| Show the topic and the question in text | Viewers who follow by reading got lost at topic changes. Every [Section] title is a corner chip for its whole section, and a question asked just before a [Pause] is a lower-third (`post.overlays.guide`) |
| An English episode shows no Arabic | The first English cut carried the Arabic sting, brand tag, source credit, disclosure and end card. Fixed strings now come from `pipeline/language.py` `ui()`; the sting has an English render (`assets/intro_sting_en.mp4`) |
| The clone is an instant voice | It takes no `<break>` tags (use `[pause]`) and no `speed`; HeyGen's free Turbo model speaks it at no credit cost |

## 11. W46-en preview review (2026-11-15)
- **Labels came up to 50 s late.** Topic chips, question labels and lower-thirds were placed from a
  words-per-minute setting and only snapped to a caption on an exact, case-sensitive match; the
  English narration ran faster than the setting. Fixed in `overlays.locate`: the first guess is the
  word's share of the way through the real captions, then it snaps to the words around it. Chapters
  (`audio.section_times`) use the same function. Test: `test_labels_follow_the_captions…`.
- **Pale and off-topic stock.** White plates and a flag, cockpit, clouds, barcode and stick figure got
  through. `keyed()` now also rejects pale plates; the tags are in `OFF_TOPIC`.
- **Still open:** stock clips that show made-up numbers (line charts, dashboards) sit beside real
  figures; the disclosure label overlaps the opening number card; no chip for Roundup and Closing.
- **Keeping attention (founder 2026-11-16).** English pace 0.94 (0.88 sounded flat); a visual longer
  than 9 s is cut into parts, each a new clip of the same search; the music bed changes key at each
  story; a soft chime lands with each number and title card. Settings: `video.voicefirst.tempo_en`,
  `visuals.max_visual_seconds`, `post.audio.music_keys`, `post.audio.accents`.

## 2026-11-17: W46-en edit and the monetisation playbook
- **Frozen picture / missing labels.** The label step broke whenever a presenter clip changed the picture's
  properties inside the cut. Enforced in `pipeline/post/overlays.py`: label images loop for the whole length
  and the step fails if the frame count changes. A length check alone does not prove the picture moves.
- **Stock with figures got through** (a bar chart tagged "hud, data, interface"). `NO_FIGURES` in
  `pipeline/post/visual_assets.py` now bans those tags; tags are still the only defence, so every preview
  is checked by eye for figures before it goes to the founder.
- **Playbook adopted.** `config/monetisation_playbook.md` is read by the writer, reviewer and critic.
  Built the same day: three title options per episode (`title_options_en` in plan.json and `titles.md`),
  and Shorts that open on a newly written line (`short_hooks` in the plan, or `reviewed/<week>/shorts.yaml`).
- **Shorts went silent at the pauses.** They are cut from the voice-only edit, so a `[Pause]` was dead air,
  and the levelling filter lifted the voice after it. `pipeline/post/shorts.py` now lays our music under
  each Short and levels the voice with one fixed gain. A frame check does not catch sound faults: trace
  the loudness of every Short before sending it.
- **W46-en missed the Microsoft 365 outage of 12 November**, which hit the Gulf. Every news search added
  the word "AI" and was built from a watched product name, so an outage of Outlook and Teams matched
  nothing. `ingestion.google_news_sites` now has two outage searches without "AI" (`raw: true`), and the
  planner is told such a story belongs in the episode when it reaches the region.
- **News was read once a week.** Until 2026-11-17 the only collection was Saturday 10:00 Gulf, looking back
  seven days. `.github/workflows/news-watch.yml` now reads every six hours, keeps what it finds in
  `data/news_watch.json` for the weekly collection, and posts big stories to the "News watch" issue.

- **2026-11-17, W46-en: the Shorts step sat for 27 and 46 minutes after the episode and its 4K master were done** (two
  runs stopped by hand, the finished episode lost with them). Not reproduced locally, cause not proven. Now each Short
  is built from its own uniform clip, every Shorts encode stops after 10 minutes and is logged, and a failed Short is
  skipped (`pipeline/post/shorts.py`). If a run still stalls there, the log names the Short and the command.

- **2026-11-17, W46-en: four stretches of empty violet screen (up to 15 s).** A stock shot with no acceptable clip gets
  our own network animation, but it only drew the first time in a run: the page is reused and the script's top-level
  `const` would not run again. Fixed with its own scope (`TECH_MOTION_HTML`). The more search terms we ban, the more
  shots land on this fallback, so it has to work every time.
- **Same review: stock clips that tags cannot catch** (clocks for "code on screen", a bar chart with figures for "server
  racks"). Each run now writes `stock_used.json` (shot, time, search, clip id) and `visuals.stock.blocklist` in
  settings bans a clip by id. After every preview: name the bad clips from that file and add them.
- **Check that preview files are fresh before measuring them.** I measured Shorts from the previous run (fetched before
  the text preview finished) and read their silences as a new fault.

- **2026-11-17, W46-en fourth edit: the label pass lost 45 of 18350 frames and the frame check stopped the run.** The
  looped label inputs fixed the missing labels, not every loss at a join. `overlays.overlay` now retries on a uniform
  re-encode of the cut when frames are lost, and stock clips are encoded with square pixels and limited range. Cause of
  the loss itself not reproduced locally.

- **2026-11-17, W46-en: the final edit was cut off by the job's own 120-minute limit** (shown as "cancelled", log not
  kept). The run before it had taken 116 minutes: 4K master about 36, labels twice when the first pass loses frames,
  slower runners in the evening. Limit raised to 210. A run shown as cancelled that nobody cancelled: check
  `timeout-minutes` first.
- **Same evening: the next run lost its runner at about two hours** ("The hosted runner lost communication with the
  server", again no log). The 4K master was the heaviest step (preset medium, 36 min). Now: the big working folders
  are deleted before it, the encoder uses `post.upload_preset` (default veryfast, short look-ahead, 4 threads; about a
  third of the time), and free disk is logged before and after. Read a failed run's annotations
  (`check-runs/<job id>/annotations`) when its log is missing: they said which of the two it was.

- **2026-11-18, founder on the W46-en Shorts:** every Short now ends with a spoken pointer ("For the full story, watch
  this week's episode on AI This Week", `assets/brand/shorts_outro_en.wav`, his cloned voice) over a longer end card
  that says the same. And a Short's picture starts on its story's own first frame even when the voice starts earlier
  in the pause: the earlier cut showed a flash of the previous shot (a green tunnel before Short 3's source card).
- **2026-11-18, W46-en publish:** YouTube went out, then the LinkedIn step failed because the publish phase had no
  ffmpeg installed. Publish now installs it, and a week whose meta has `youtube_video_id` skips the YouTube upload so a
  re-run only posts to the other channels (never upload the same episode twice).
- **2026-11-18, first breaking Short:** a source card with a long headline is cropped mid-word in the vertical frame
  ("…caused by a malign a"). In breaking Shorts use a short title card instead of a long-headline source card.
- **2026-11-18: the voice step runs on its own.** When a week has no `reviewed/<week>/voice.yaml`, assemble voices
  every chunk through HeyGen's API (`pipeline/video/tts.py`, POST /v3/models/audio/tts, the cloned English voice) and
  writes `output/<week>/voice.yaml`. Face chunks become narration (no presenter video is made automatically).
- **2026-11-18, W46-en chapters:** every chapter in YouTube's chapter list showed the video thumbnail. The check
  (`scripts/youtube_video_check.py`, workflow `video-check`) found processing finished but no frame previews yet; chapter
  pictures come from those, and no API sets them. Fix for good: `publish.chapter_gate`. The episode is uploaded
  unlisted, and `release` (every 20 min) makes it public at the release time only once each chapter has its own
  picture (or after `chapter_wait_hours`, and says so). Upload well before the release time so YouTube has finished.
- **2026-11-18, automatic voice test:** the voice took 10 seconds; the run took 39 minutes because Whisper spent 35
  minutes revalidating its cached model with the Hugging Face hub. The render job now sets `HF_HUB_OFFLINE=1` when the
  model came from the cache.
- **2026-11-18: breaking Shorts are drafted on their own.** After each news watch, `scripts/breaking.py` drafts a Short
  from the strongest new flagged story (Claude, from the collected article text only), checks it (every line cites an
  article, figures found in the cited text, a second model judges each line, no advice), writes
  `reviewed/<date>-brk-<slug>-en/`, renders it, and posts the script and the video link on the "Breaking Shorts" issue.
  Nothing posts until the founder replies `post <week>` there (workflow `breaking-post`, owner only).

- **2026-11-18 — first automatic breaking Short failed in Whisper.** `HF_HUB_OFFLINE=1` on a Whisper cache hit refused to download a model size the cache did not hold. Fix: `transcribe_words` loads with `local_files_only=True` and downloads only on a miss; the env switch is gone (`pipeline/post/subtitles.py`, `weekly.yml`).

- **2026-11-18 — the chapter-picture check was blind.** From GitHub runners YouTube serves the W46 watch page behind "Sign in to confirm you're not a bot" (`LOGIN_REQUIRED`), which strips the frame previews, so every chapter showed the thumbnail there whatever viewers saw (a control video from the same runners was served normally; the API reports W46 processed, public, not age-restricted). The check now says UNKNOWN behind the wall instead of FAIL, and the release gate falls back to its time limit. Storyboard image URLs need a signature (403), so they cannot be probed directly. A human look in a browser is the only verdict when the wall is up.

- **2026-11-18 — a rewritten Short kept its old voice.** The render restores the last run's `output/`, so the old `voice_pack.json` and automatic `voice.yaml` were reused after the script gained the founder's view (similarity 0.46 was the tell). Now the pack is rebuilt when `script.md` changes (`voice_pack.src` stamp) and each automatic chunk carries a `text_sha`; a mismatch voices it again (`run_pipeline.py` phase_assemble, `pipeline/video/tts.py`).

- **2026-11-18 — "Face" alone on screen.** Captions broke at 42 characters wherever they fell, leaving "…platform Hugging" then "Face" by itself. Now a caption never breaks between two capitalised Latin words (a name) or before a sentence tail of one or two short words; the line may run up to a third over (`_keep_with_next` in `pipeline/post/subtitles.py`, test in `tests/test_captions.py`).

- **2026-11-19 — news watch half blind.** Google News refused the regional `site:` searches (429) every run and two newsletter feeds answered 403. Now searches are spaced (≥ 2 s), retried once after 20 s, and stop for the run after a second 429 (`_Throttle`, `pipeline/ingestion/watch_sources.py`); Import AI reads the author's own feed, The Batch comes through a Google News site search.
- **2026-11-19 — automatic Short check.** `scripts/short_check.py` (length, loudness, peak, dead air, frozen picture, lone caption words, long captions) runs on every breaking and weekly Short; its verdict is in the "ready" comment.
- **2026-11-19 — thumbnail B.** Every episode now also makes `thumbnail_b.png` (other words from `thumbnail_text_b_en`, and the opposite face choice) for YouTube's Test & Compare; the API cannot start a test, so the founder adds B in Studio. Links are in the "ready" comment.
- **2026-11-19 — first Shorts numbers.** "Jensen Huang Leaves NVIDIA" drew 49 views, the others 0–11 (breaking Shorts 0 on YouTube so far). Small sample, so two cheap changes only: the voice now starts after a 1.5 s opening card instead of 2.5 s (`post.shorts.hook_seconds`), and breaking titles lead with the person or company and the action. Revisit with Monday's numbers.
