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
- **2026-11-19, W46-en chapters re-checked in a signed-in browser:** about 1.5 days after upload, all 10 chapters
  still use `hqdefault.jpg` (the video thumbnail), and the GitHub runner check now meets YouTube's sign-in wall
  (UNKNOWN). Time alone has not produced chapter pictures for this upload, so the gate may often hit
  `chapter_wait_hours` and publish anyway. Watch W47: if its chapters also never get pictures, the gate's premise is
  wrong and the wait only delays the episode.
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

- **2026-11-19, duplicate TikTok post traced (ADNOC/G42 Short, posted 17 Nov 17:19 and 17:25 UTC):** two causes.
  (1) TikTok had accepted the upload when the run errored (`dict.update() got multiple values for keyword argument
  'status'`); `post_due` counted any error as "not posted", so the next run sent it again. (2) The queue save hit a
  git conflict on `data/social_queue.json` and the push loop gave up silently, losing the "posted" record. Fixes:
  an error after the platform has the file is `Unconfirmed` → status `unconfirmed`, never retried automatically,
  reported with ⚠️ (TikTok status-check timeouts and lost status calls included); the result is recorded before
  anything else; `scripts/save_queue.sh` merges this run's results onto main on a conflict (`social.py merge`) and
  fails the step if it still cannot push. Tests in `tests/test_social.py`.
- **2026-11-20, TikTok after going public:** the Anthropic breaking Short failed on TikTok with `unaudited_client_can_only_post_to_private_accounts`. An app TikTok has not reviewed may post only to private accounts, so making @aithisweek public (19 Nov) ended automatic TikTok posting. Options: TikTok app review (developers.tiktok.com, Content Posting API audit), or upload by hand in TikTok Studio. YouTube and LinkedIn are unaffected.
- **2026-11-20, repeated breaking drafts:** the news watch drafted five more Shorts on the outage after it was posted, because a story counted as done only by its exact headline. Fixed with `pipeline/story_match.is_repeat` (two shared key words with a headline drafted in the last `breaking.repeat_days`).
- **2026-11-20, W47 script run cut off:** the scheduled run was cancelled at its 60-minute limit before writing a script. The week's news pile reached 2,679 items, and the radar tagged them in 134 Haiku batches one after another (43 min). The tag cache sat in `output/<week>/`, which CI never keeps, so nothing was reused. Fixed: batches go out 8 at a time (`radar.extraction.workers`), the cache is `data/radar_tags.json` (committed with the radar state, pruned to the current run's items), and the script job's limit is 90 minutes. Tests in `tests/test_radar.py`.
- **2026-11-20, W47 critic cut off:** with tagging fixed (5.5 min), the re-run failed after review pass 1 with `critic stopped early: max_tokens`. The critic allowed 8,000 output tokens, but Opus 5.5 always thinks and thinking counts against that limit. Raised to 16,000 (the source map's limit, still under the SDK's non-streaming ceiling). Test in `tests/test_script_quality.py`.
- **2026-11-20, W47 left out the Anthropic IPO:** the script ran, but its 30 seats went to 8 AWS blog posts, 6 NVIDIA posts and GitHub release notes (scores 14–21). The IPO scored about 11, although 117 articles in WIRED, CNBC, NYT, WSJ and Reuters covered it: the scorer rewarded keyword density and never counted how widely a story was covered. Fixed in `pipeline/ingestion/scoring.py`: a story-size bonus (`coverage_bonus` × log2 of the outlets carrying it; headlines that share two key words are one story), at most 3 seats per source and 2 per story, and 3 seats reserved for stories the news watch flagged. On this week's pile the IPO ranks 2nd and 4th. Tests in `tests/test_selection.py`.
- **2026-11-20, W47-en render refused (10 "unsourced" claims):** the sources for the hand-added lines ($83 IPO price, 17% close, HUMAIN, California) sat in `reviewed/2026-W47/items.json`, but `scripts/apply_reviewed.py` merged reviewed items by an `id` key that saved items never carry (the id is computed from the url), so nothing was merged and the English source map could not find them. Now merged by url (`tests/test_visual_edit.py`), and the English source map also searches every item the script shows a source card for, since a story added by hand is never in the plan (`tests/test_translate.py`).
- **2026-11-20, W47-en voice refused by HeyGen:** the first whole episode voiced through HeyGen's API (`pipeline/video/tts.py`) failed with HTTP 400 "break tags are not supported for instant voice clones"; W46-en had been voiced by hand through the connector, which accepts them. When HeyGen gives that error, the chunk is re-sent with its pauses as "...". Test in `tests/test_tts.py`.
- **2026-11-20, legal flags (founder: "anything that puts us at legal risk, we need to highlight"):** `pipeline/scripting/legal.py` reads each source map and writes `legal.md`: allegations against someone on one weak outlet, investment imperatives, rulers/religion/state next to a negative claim, quotes without direct support. The Review issue shows them; a render refuses while a major flag is not answered by number in `reviewed/<week>/legal_ok.txt`. Deterministic word lists, not legal advice. On W47 it caught the Cursor/Fireworks breach line we had cut by hand. Breaking Shorts have no source map yet, so they are not checked. Tests in `tests/test_legal.py`.
- **2026-11-20, visuals (founder: "real photos… more animations… digital, then real, then digital"):** W47 used 83 stock shots, "neural network animation" 8 times. New shot kinds: `[Visual: photo <subject>]`, a Wikimedia Commons photo taken only under CC0/PD/CC BY/CC BY-SA, credited with author and licence, framed over a blurred copy, and a title card when none exists; and `[Visual: generated <scene>]`, our own generated clips listed in reviewed/<week>/visuals.yaml (stock until then), never a real person. The shot list flags a stock search used twice and more than two digital shots in a row, and lists the clips to generate. Tests in `tests/test_photos.py`.
- **2026-11-20, W47-en founder review (rules for every episode):** (1) the Welcome line introduces the host by full name and bio (`publish.host_intro_ar/en`, added by `script_format.ensure_host_intro`), and a render refuses face chunks without a presenter video (`visuals.require_face`): W47-en first went out faceless because automatic voicing makes speech only; (2) stories covered in the last 4 episodes (`data/covered.json`, written by the script phase) are marked down in ranking and listed to the editor, to come back only with something substantially new; (3) Africa and Türkiye each get a seat when they have AI news (`scoring.min_per_region`), replacing the 2026-11-15 "no quota". Tests in `tests/test_w48_rules.py`.
- **2026-11-21, W47-en full review:** (1) sources added to the Arabic week after translation never reached the English render (blank "Source" cards): `apply_reviewed.py` now merges `reviewed/<week>/items.json` into the `-en` week too; (2) 26 of 95 stock shots became a bare animation because 13 search phrases were reused up to 8 times and the no-repeat rule ran them dry: an exhausted search now tries shorter searches first (`visual_assets.broader_queries`), and W47's repeated phrases were given unique words; (3) card titles drop emoji (`card_title`); (4) six off-tone clips blocked, and real licensed photos (Westminster, Nadella, Amodei, Bonta, Hassabis, Abu Dhabi) placed where people are named. A suspected Short cut mid-sentence was a sampling artefact: check the last seconds before calling a cut. Tests in `tests/test_visual_edit.py`.
- **2026-11-21, alerts to WhatsApp:** CallMeBot was planned, but the founder already runs a whatsmeow bridge on his Mac (localhost:8080) for Mac-health, NAS and bill messages. GitHub cannot reach it, so a Mac relay (`scripts/mac_alert_relay.py`, launchd every 10 min) polls the repo with `gh` and sends through the founder's own `whatsapp_monitor.py` functions (one implementation). It reads only the owner's and the pipeline bot's issues and comments: the repo is public. Tests in `tests/test_mac_alert_relay.py`.
- **2026-11-21, stale preview video on #52:** the chain started two preview runs (`what=video`, then `what=text` for the Shorts) in one concurrency group. GitHub keeps only one *waiting* run per group, so the second replaced the first, even with `cancel-in-progress: false`: the Shorts and files were new, the episode MP4 was last night's (byte-identical, 882 s instead of 895 s). Now one `what=all` run does both. Check a preview's length against the render log's "final" length before calling it ready. Test in `tests/test_ci_workflows.py`.
- **2026-11-21, W47-en founder review 2:** (1) the Microsoft view was rewritten in the founder's own argument (early movers with models two or three versions ahead should find and patch bugs faster than any amateur) plus the open question of lawsuits and who pays; (2) two repeats cut: ADNOC/G42/OpenAI (W45) and ChatGPT's wallet (W46), kept as one "last week we covered…" line; (3) photos: a Commons photo must name its subject in the file title ("OpenAI headquarters" had matched the European Southern Observatory), `File:` names an exact checked file, and `avoid` skips files used before; head-office photos for NVIDIA, Google, Alibaba and Amazon; (4) a ghostly walking figure and an abandoned roller coaster blocked. Tests in `tests/test_photos.py`.

## 2026-11-21: render speed (W47-en timing runs, 65 → 34 min)
| Lesson | What happened | Now enforced by |
|---|---|---|
| Measure before optimising | Merging the 1080p and 4K encodes into one pass saved nothing (24 min either way): the 4-CPU runner is CPU-bound, so one decode less or jobs side by side do not help | `pipeline/timing.py` → `timings.json` + run summary table every render |
| The preset is the cost, CRF is the quality | 1080p `medium`/`slow` cost as much CPU as the whole 4K encode. By SSIM against the source, 1080p veryfast crf 16 = medium crf 18, and 4K superfast crf 18 beats veryfast crf 18 | `post.final_preset/final_crf/upload_preset` (settings.yaml) |
| A looped image is decoded every frame | 26 cue cards at `-loop 1 -framerate 2` = ~45,000 PNG decodes: most of the 10-min card pass | `overlays.card_graph` (each card decoded once) |
| …and a filter rebuild drops an image read once | First fix lost the last label at a presenter join (colour tags differ → chain rebuilt); the label check stopped the run | `-reinit_filter 0` on the cut; `test_cards_survive_a_filter_rebuild_at_a_join` |
| A timing run must not touch the week | The first test render queued in the week's group and was cancelled | `test_run` input: own queue, `test-week-*` artifact, no report/chain/preview/alert |

## 2026-11-22: W47-en rework — change a segment, never the whole video (founder)
- **Rule:** a review change re-makes only the segment it touches: re-voice only the changed chunks, re-make
  only the face clips whose audio changed, keep every approved clip (stock pins, generated clips, photos,
  face clips). W47 cost 148 HeyGen credits because faces were re-made twice for new looks; a normal
  episode is ~100–110.
- **Gap still open:** the render rebuilds the whole episode (~2.5 h) even for a one-segment change; a
  segment render (rebuild the changed segment, splice it at its section boundary) is the next build.
- **Stock pins:** a re-render re-searched Pixabay and swapped 9 of 59 approved clips. Fixed with
  reviewed/<week>/stock_pins.json (visual_assets.stock_pins / fetch_pinned).
- **Quality:** the founder rated the generated HeyGen clips (house palette, made for the line) far above
  stock. Generated clips are the default from W48; stock is the fallback.
- **Higgsfield:** deferred by the founder (2026-11-22); revisit for a few cinematic showcase shots, PLUS monthly.

## 2026-11-22: story ranking — stories are ranked, not articles (founder-approved plan)
Plan: `docs/plans/2026-11-22-news-ranking.md`. Why: 17 new regional outlets add ~80 AI items a week, and W47's
30 seats had gone to vendor blog posts while a 117-article story was left out.
- **Rank stories, never articles.** `pipeline/ranking/cluster.py` groups the scored week into at most 20
  stories. The outlet count is shown and feeds the evidence score; it never multiplies a total (test:
  `test_many_outlets_on_one_story…`).
- **The model scores, the code adds.** `judge.py` returns 0–3 per criterion with a reason; its schema has no
  field for a sum. `rank.py` applies the weights (×3, ×2, ×1, ×1), the gates and the slots. A regional
  consequence of 2 or 3 is cut to 1 unless the named actor is found in the story's own sources.
- **Gates are pass/fail, not scores:** new since the last episode, a tier A/B outlet, enough for 60–180 s, not on
  the kill list. A failed story can be radar; a repeat with nothing new is out; a generic explainer goes to Shorts.
- **Shorts lines and the thesis carry no figure the sources do not** (`_invented_numbers`); such a candidate is dropped.
- **The founder decides before the script.** The "Ranking: <week>" issue shows scores and reasons;
  `/story <id> <slot|drop|auto> because <reason>` and `/story approve` (`story-decide.yml`, owner only). Every
  decision is logged in `data/ranking/<week>.json` and a change after approval needs a new approval.
- **One story = one unit, end to end:** the story id is on the plan segment (`story_id`), and the planner's
  segments are put in the approved order in code (`rank.align_plan`), whatever order the model wrote.
- **A story must keep the article it is named after (2026-11-23).** Choosing a story's articles by outlet tier
  alone dropped the lead article of a 47-outlet story; the link, the named-actor test and the writer all then
  read a different article. Enforced in `cluster.cluster`; test `test_the_article_a_story_is_named_after…`.
- **Channel rules that must never bend are code, not a judge's opinion (2026-11-23):** buy-or-sell headlines
  and routine version releases are flagged in `cluster.py` and gated in `rank.score`, whichever judge ran.
- **A review issue leads with the decision (2026-11-23).** The first Ranking report was three ten-column tables;
  what the founder has to weigh (a seat holding a slot at 8/21 over a 15-point story, two stories on one
  company) was only visible by comparing rows. `rank.checks` computes those lines and they come first.
- **A review issue is used from a phone (2026-11-23).** Typing `/story sfa3d quick because …` with a random id,
  one comment per move, and getting 17,000 characters back each time was the slow part. Numbers, several lines
  per comment, a short reply and one list kept current in the issue body: `scripts/story_comment.py`,
  `story-decide.yml`. A number is looked up in the list as it was shown, before anything moves, and one bad line
  applies nothing: tests `test_numbers_mean_the_list_as_it_was_shown…`.
- **A silent install failure looked like success** while building this: `pip install … > log; echo $?` inside a
  longer command reported the last command's status, and Python 3.15 had no wheel for a pinned package. Use
  Python 3.12 locally (what CI uses) and check the install by importing a package.

## 2026-11-22: W47-en release day
- **The release gate held the episode 1 h 40 min past its slot.** Every runner check met YouTube's sign-in wall, and the gate treated "cannot see" as "not ready". Fixed in `scripts/release.py`: a blind check releases at the release time and says so (test in `tests/test_release.py`).
- **LinkedIn was skipped without a word.** `phase_announce` posts only when `linkedin_post_en` exists (W46 had it in `reviewed/<week>/meta.yaml`; W47 had none) and logs nothing otherwise. Open: write the post text with the publish pack, and make a missing text fail loudly.
- **Facebook Page post by hand** in Meta Business Suite (composer, Instagram unticked, caption plus link). Instagram needs the Short's video file on the Mac; the browser upload takes 10 MB at most.
- **Source links in the description were too long** (founder): Google News redirect links ran to 278 characters. `publish/description.py` now writes the publisher's own link without tracking parameters (`short_sources`, `clean_url`; tests in `tests/test_short_links.py`). No link shortener: the viewer should see the outlet's domain.
- **Meta's developer sign-up never sent its SMS code** (two UAE numbers, both "Not confirmed" on the account), so the direct Instagram and Facebook route had no token. Founder 2026-11-22: post through Buffer instead (this replaces "no third-party service" of 2026-11-13 for these two platforms only). `social.Buffer` posts each Short as an Instagram Reel and a Facebook Page Reel from its public release URL, and the episode as a Facebook link post in `phase_announce`; it reads the post's status back until `sent`, and a post still sending at the deadline is `unconfirmed`, never retried. Needs one secret, `BUFFER_API_KEY`; the direct route wins when its own tokens exist. `connect` check lists the Buffer channels. Not yet proven on a real post: Buffer fetching a GitHub release link (it redirects) and Facebook Reels over 60 s.
- **Composio, not Buffer, carries Instagram and the Facebook Page** (founder, same day: he already has a Composio account and wants the smallest footprint; nothing was connected to the Page before). `social.Composio` calls Composio's REST execute endpoint: Instagram Reel (container, publish, permalink), Facebook Page Reel (marked AI-generated) and the episode's Facebook link post. Secrets: `COMPOSIO_API_KEY`, and `COMPOSIO_USER_ID` when the connections sit under a named user. Order: the platform's own token, then Composio, then Buffer (`social.relay`). A publish call with no answer or no id back is `unconfirmed`, never retried. Instagram gets no AI-generated flag this way (Composio has no field for it), so the caption's disclosure line is the only label there. Proven 2026-11-22 on W46-en Short 1 (instagram.com/reel/DgDXalEmdRh): the posting permission, `ig_user_id: me`, hashtags in the caption and a release link that redirects all work for Instagram. The API key must be created with "Tool execution (Legacy): write" (off by default, and a key's permissions cannot be changed later). Connecting a platform makes every approved, overdue queue entry for it post on the next hourly run: seven old Shorts were held (`skipped` with a note) before that happened. Not yet proven: a Facebook Page Reel and the episode link post.

## 2026-11-23: health check — a silent failure must not look like a quiet day
- 200 runs were green while only the weekly job told anyone about a failure. A refused sign-in, a post dropped after
  three tries (status `skipped` with an `error`) and a stopped news watch all looked like nothing to do.
- **Enforced in:** `.github/workflows/health.yml` + `scripts/health.py` + `pipeline/publish/health.py`. Daily 07:07
  Gulf: connections by identity (first run records who each sign-in reaches in `data/health.json`; a different or
  missing account later is an alert), the posting queue, the news watch's last run and item count, and each scheduled
  workflow's last SUCCESS against `health.max_age_hours` in settings. On-demand workflows alert the moment they fail.
  One issue, "Health: needs a look"; it closes itself when all is clear.
- **Kept honest by tests:** a new workflow fails `tests/test_health.py` until it is either scheduled with a limit in
  settings or named in health.yml's `workflow_run` list.

## 2026-11-23: the episode's announcement — once per channel, and never silently missing

- **What happened (W47-en):** the first announce run posted nothing and finished green (the plan had no announcement
  text). The second posted to LinkedIn; the Facebook Page got nothing and the log did not say so. Nothing recorded the
  LinkedIn post, so a third run would have posted the episode there twice.
- **Fix, and where it is enforced:** `pipeline/publish/announce.py` posts each channel once and keeps the result in
  `data/announced.json` (committed by weekly.yml even when the run fails). Missing text or a failed channel fails the
  announce run, which raises the usual run-failed alert. `tests/test_announce.py`.
- **Also:** the connection report no longer says "Instagram: not connected" when Composio carries it, and the
  breaking-Short message names the channels from settings (TikTok as drafts).
- **Not done:** TikTok has no identity check. Its sign-in changes on every use, so a second job reading it could
  break posting; it stays "sign-in saved".

## 2026-11-23: what a face clip costs on HeyGen's API (measured, one clip)

- Workflow `heygen-cost`, action `face-test`: look D v3 as a still image plus a W47 sound file, POST /v3/videos
  (`type: image`, 1080p, default engine). **$0.40 for 10.06 s**, ready in 101 s. Wallet 1.68 → 1.28 USD.
- W47-en had 11 face clips, 53.7 s in all: about **$2.13 an episode** at that rate. One data point: whether HeyGen
  bills by the second or in blocks is not known.
- The API key spends a prepaid USD wallet (auto-reload off), separate from the plan credits the connector spends.
  Speech from the API comes out of the same wallet; an empty wallet refuses the call (HTTP 402).
- GET /v3/usage returned an empty list although calls had been made: do not rely on it for charges; read the wallet.
- **2026-11-23: face clips run on their own.** When a week has no `reviewed/<week>/voice.yaml`, assemble makes
  the face clips through the API after the speech (`pipeline/video/faces.py`, `video.heygen.auto_faces`), from
  `face_image`. A clip is asked for once (Idempotency-Key = picture + sound), each finished clip is written to
  voice.yaml at once, and the phase refuses before spending when the wallet holds less than 1.25 × the estimate.
  A hand-made voice file under reviewed/ is still used exactly as it is. The daily health check warns when the
  wallet is under `health.heygen_min_usd`. Tests in `tests/test_faces.py`. Not yet run on a real episode.

## 2026-11-23: story grouping, measured on the live W48 items before Friday's first ranked run

- **Verbs were tying unrelated stories together.** Any two shared headline words made one story, so ServiceNow
  items ("raises … sees") sat inside an IMF story, and "Saudi Arabia announces new tax" inside the SDAIA
  universities story. A story's articles go to the writer as its sources, so this could put the wrong source under
  a story. Fix (`pipeline/ranking/cluster.py`): one shared word must be a name (capitalised inside sentence-case
  headlines), and two words that name one thing ("Saudi Arabia", "Wall Street") count once.
- **One event was told as several stories** (the Anthropic IPO: four of the top 30). Joining them by headline
  words was tried two ways (a story's repeated words; votes between members) and both lumped unrelated Microsoft,
  Google and Nvidia stories together. So the judge now names a story that reports the same event as an earlier
  one (`same_event_as`) and `rank.merge_same` joins them in code. Not yet seen on a live judge run.
- Tests in `tests/test_ranking.py`. Still in the live list: off-topic items the AI filter lets through (an
  archaeology story, climate talks) and newsletter round-ups ("Morning Briefing").
- **2026-11-23, two dry runs with the live judge (workflow `rank-dry`, prints only):** left optional, the
  same-event answer came back empty and nothing was joined; made required with an example, the judge joined
  exactly the three extra Anthropic IPO stories (20 → 17) and nothing else. Seen in the same runs and NOT fixed:
  the judge's totals moved between two runs on the same items (SDAIA 16 → 9), the IPO story was killed as "no
  regional consequence" with Abu Dhabi's MGX in its headline, and an off-topic climate-talks item took a Quick
  slot. Read Friday's ranking with that in mind before approving it.

## 2026-11-23: messages about where a release goes are built from the code that sends it
A read-only check found the founder could not tell from the pipeline's messages where anything went. The
`publish` reply named only LinkedIn and Facebook and said "unlisted" while the setting is private; the "ready"
message named every configured platform, connected or not; a platform with no secrets was skipped at info level;
WhatsApp alerts had been off for weeks with nothing saying so; `docs/SOCIAL.md` still said no third-party
service, TikTok private, and Facebook native video.
- **One table of secrets, one status function** (`pipeline/publish/release_status.py`). `social.posters`, the
  `publish` reply (`scripts/release_plan.py`) and `channels_line` read it. Test: `tests/test_release_status.py`.
- **Off is allowed, silently off is not.** A skipped platform is a warning, a `⏭️` line and a note on the queue
  entry; alerts that are off log once per run and add a note to the health report.
- **A workflow that only needs to know whether a secret is set gets a flag, not the secret**
  (`${{ secrets.X != '' && '1' || '' }}` in `approve.yml`).
- **A message hard-coded in a workflow drifts.** The old reply was a shell string; the new one is printed by code.

## 2026-11-23: chapter pictures — YouTube makes them days late; our gate could never have helped

- **Measured from the founder's Mac (no sign-in wall there):** W47-en, one day after going public, has its frame
  previews and 11 chapters, every chapter still on the main thumbnail (`hqdefault.jpg`). W46-en, which looked the
  same 1.5 days after upload, now has its own picture on all 10 chapters (`hqdefault_<ms>.jpg`). Other channels'
  chaptered videos from the same search: those two to three days old have their own pictures (one with 6 views);
  those under a day old do not; one three-day-old 3-minute video still does not.
- **So:** the pictures arrive roughly two to five days after publishing, whatever the channel, and nothing in the
  upload or the API sets them. The 2026-11-18 premise ("wait a few hours") was wrong by an order of magnitude:
  `publish.chapter_gate` cannot produce them and only risks a late release (W47-en went out at 18:40 Gulf, not
  17:00). Not known: whether the clock starts at upload or at going public.
- The check from GitHub runners is still blind (sign-in wall). Run `python scripts/youtube_video_check.py <id>`
  from the Mac for a real answer.
- **2026-11-23, HeyGen's API price list** (platform.heygen.com/pricing, readable only in a signed-in browser):
  Avatar 4 photo avatar $0.0385/s (Avatar 3 photo avatar $0.0165/s, the engine whose lip sync we rejected);
  speech $15 per million characters, at 50% off until 1 December 2026. W47-en at those rates: 14,939 characters
  of speech $0.22 and 53.7 s of face $2.07, about $2.29 an episode. HeyGen's docs give no supported way for an
  unattended job to spend plan credits: OAuth (the connector, `heygen auth login --oauth`) needs a browser
  sign-in and is described as for small trials; an API key always bills the prepaid wallet.

## 2026-11-23: explainer Shorts; and a weekly-Shorts mistake

- **Mistake:** the W47-en episode clips were queued and put to the founder for approval although the playbook has
  said since 2026-11-18 that weekly Shorts are off ("old news"). They were held before anything posted. Before
  queuing or proposing any post, read `config/monetisation_playbook.md`; `tests/test_release_status.py` now fails
  when an unapproved weekly Short waits in the queue.
- **Explainer Shorts built** (`pipeline/explainer.py`, workflow `explainer`): approving the ranking starts them.
  They reuse the breaking route (drafting, figure check, second-model check, render, `post <id>`), with their own
  instructions and a check that rejects words that date the Short. `explainer.max_per_week` is 2.
- Not checked: the spoken outro file is the breaking one (`shorts_outro_breaking_en.wav`); listen to the first
  explainer before posting it. Neither kind of Short goes through the legal flags yet.

## 2026-11-23: viewer feedback on structure (fact vs analysis, the end user, a closing bottom line)

- A colleague asked for facts first and all analysis after; viewers praised the regional take and asked for the
  end user's angle. Decided: analysis stays next to its story, but every deep story marks the switch (spoken line
  and a «شو يعني؟» card), "why it matters" carries one end-user line where honest, and a 45 to 60 second
  «خلاصة الأسبوع» closes the episode before the sign-off.
- Enforced in `config/monetisation_playbook.md` (Length and shape), the running-order brief (`rank.brief`,
  tested), the writer's structure prompt and both critic rubrics. First real use: the W48 episode; check that the
  bottom line holds no new figure and that the episode stays inside its length.

## 2026-11-23: HeyGen engines side by side (measured, workflow `heygen-cost`, action `face-compare`)

- Same still (look D v3) and same sound, 8 s English and 9.3 s Arabic. Charged from the API wallet:
  Avatar IV $0.28 and $0.35 (about $0.035 to $0.038 a second); Avatar 6 $0.70 and $0.90 (about $0.09 to $0.10 a
  second, 2.5 times Avatar IV); precision lip-sync of a finished clip $0.24 and $0.28 (about $0.03 a second, on
  top of the clip). The whole test, speech included: $3.45.
- `{"engine": {"type": "heygen-avatar-6"}}` IS accepted on `type: image` requests (HeyGen's Avatar 6 guide says it
  is not; the schema is right), and so is a top-level `motion_prompt` with it. All clips came back 1906×1080, 25 fps.
- Not decided: which looks best is the founder's call from the clips (`output/heygen_compare/`, not committed).
  The show still renders on Avatar IV.

## 2026-11-23: face clips moved to Avatar 6 (founder's choice after the side-by-side)
- `video.heygen.face_engine: heygen-avatar-6`; `faces.make_face` sends it and puts it in the once-only key, so a
  clip asked for again on another engine is a new clip. Remove the setting to return to Avatar IV.
- `face_usd_per_second` is 0.10 (measured $0.089 to $0.098). About 54 s of face costs about $5.40 per language,
  $6.75 with the wallet margin. The health floor rose to $15 so the warning comes before a render is refused.
- Clips already in a week's `voice.yaml` are kept as they are; only missing or expired ones are made on Avatar 6.
- Enforced by `tests/test_faces.py` (engine sent, engine read from settings, price not under the measured one).

## 2026-11-24: an outage is not news by itself (founder; the AWS alert-delay Short, dropped)
- What happened: the watch drafted a Short on an AWS outage that was nine days old, from one trade site, with no
  count of who was affected. It would have been the fourth outage Short in a week.
- Rule: measure the impact before giving an outage airtime. Outages matter, but not every one goes on everything.
- Fix: `breaking.outage_unmeasured`: an outage headline is drafted only when an article gives a count of who was
  hit (users, customers, flights, reports...) or `breaking.outage_min_sources` (3) outlets carry it. Otherwise it is
  recorded as skipped with the reason. The writer's rules also ask for the measured impact in the first three lines.
- Not covered in code: the age of the outage itself (the article was new, the outage was not). Check the date by eye.
- Enforced by `tests/test_breaking.py` (outage section, using the dropped AWS story's own article).

## 2026-11-24: the Shorts at 1.08 were too fast (founder)
- Cause: yesterday's fix sped the whole Short up by one number (0.94 to 1.08). One quick pace from start to end
  is tiring and the opening line goes by before it lands.
- Fix: the middle of a Short plays at `tempo_short_en: 1.04`; the opening line and the closing line play at
  that x `pace_short_ends: 0.9` (0.94, the episode's pace). The lines are found by the pauses in the speech
  (`voicefirst.pace_plan`); a read with no clear pause keeps one pace. Face clips keep one tempo (lip sync).
- Not yet heard on a real Short. Speed still does not add energy: that needs a livelier clone.
- Enforced by `tests/test_breaking.py` (tempo never above 1.05; first and last line slower).

## 2026-11-23: viewers found the Shorts slow
- Cause: Shorts inherited the episode's delivery. English speech ran at tempo 0.94, about 133 words a minute, with
  one picture every 6 to 7 s and an 18-word opening line (the OpenAI Short of 2026-11-23).
- Fix: `tempo_short_en: 1.08` for Shorts only (`voicefirst.for_short`, used when the folder has `breaking.yaml`);
  9 to 12 lines of 14 words at most, first line 10 at most (`breaking.SHAPE`, shared with explainer Shorts;
  `mechanical()` rejects a draft outside it).
- Not yet heard: the first Short drafted after this is the test. Speed does not add energy to the voice: the clone
  copies its calm sample. A livelier voice needs HeyGen's expressiveness setting (untried) or a clone recorded
  in a livelier delivery.
- Enforced by `tests/test_breaking.py` (pace section).

- **2026-11-23 — "Jensen Huang returns as CEO" got no breaking Short.** Two causes: three smaller stories had used the day's limit of 3, and the flagged headlines (Gulf Business, Gulf News) had no article text, so no draft could be fact-checked. Now a story carried by 5+ outlets at once goes past the limit (up to 2 extra a day: `breaking.big_story_sources`, `big_story_extra`), and a flagged story pulls in the same story from unflagged outlets for its text (`pipeline/breaking.py`).

## Dashboard reel numbers (2026-11-24)
- Instagram and Facebook post through Composio, so the dashboard reads their numbers there too
  (`scripts/channel.py` `composio_stats`). Composio's Meta app returns Instagram **likes** only:
  media insights (views) answer "Application does not have permission for this action", and
  Facebook reels have no post insights through its tools. Views for those two need the founder's
  own Meta app tokens (`INSTAGRAM_TOKEN`, `FACEBOOK_PAGE_TOKEN`), which `platform_stats` already uses when set.
- YouTube Analytics has no hour-of-day dimension: the dashboard's "best day" is by weekday only.
