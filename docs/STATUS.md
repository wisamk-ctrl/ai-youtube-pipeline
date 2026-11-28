# Status and handoff — 2026-11-12

> Newest first: read "Own-voice route" at the end and `docs/LESSONS.md` §8–9. The corner circle and
> the HeyGen render notes below are history; the founder reads the script himself (2026-11-08).

Where the channel stands, so any new session (cloud or on the founder's computer) picks up
here. Standards live in `CLAUDE.md`, `config/style_guide.md` and `config/visual_standard.md`.

## Done and working
- **Pipeline end to end on GitHub Actions** (repo is public, so Actions minutes are free):
  ingest → plan → Jordanian script → critic → source map → director → (HeyGen render) →
  import → edit → cue cards → script-exact subtitles → preview.
- **Language:** Jordanian colloquial (urban Ammani); the critic enforces it.
- **Look:** face full-frame 10–20 %, tech/AI animation the house look, presenter in the corner
  circle for presence; Pixabay animations first, generated network animation as fallback.
- **Sourcing:** the source map checks the full article text the writer saw (the 1,500-character
  false alarm is fixed).
- **Presenter (2026-11-07):** the landscape look "Professional in blue shirt" (`1df5311275d0482cbe916ab841005526`,
  a photo look, 2752×1536) replaces the portrait twin "Sam -- 1" (`dd64d6001c4e41c5a91b2fb9eead42a6`). Jordanian voice
  clone `4c810d9c9906445f81dfd4f7d32259e0`, both in `config/settings.yaml`.
- **Secrets on the repo:** ANTHROPIC_API_KEY, YOUTUBE_API_KEY, HEYGEN_API_KEY, PIXABAY_API_KEY.
- **Render route:** manual (HeyGen web app on the monthly plan; API credits not bought).

## First full episode — 2026-W45 (2026-11-07)
- Rendered through the HeyGen connector from this chat: look "Professional in blue shirt",
  voice clone, Avatar III, 1080p, 8 min 57 s, 63 credits (`94712b9100228d97e2a8736f5bee467e`).
- Imported and edited (run 42393605088): transcript matches the approved script at 0.94,
  face 10 %, 82 shots, every visual made, 46 Pixabay clips. 1080p master `final_subtitled.mp4`
  in the `week-2026-W45` artifact; 720p preview on the `previews` branch.
- Founder review: lip sync off, words mispronounced or said twice, the corner circle looks wrong.
  The inspect report (issue #15) traced the speech faults to the written script: names written in
  both scripts were read twice, bracketed English glosses were read aloud, vowel marks were misread
  («بُعد» → «بوعد»), and G42 / Claude / HUMAIN were mispronounced.
- Fixed (2026-11-07): `speakable()` in `pipeline/script_format.py` now shapes the voice text only
  (paste pack and API): a name followed by its English spelling is said once, bracketed English is
  dropped, harakat except shadda are stripped, and `config/pronunciation.yaml` respells hard
  names. Subtitles keep the full written script. The corner circle is switched off.
- Lip sync: the edit takes video and audio from the same HeyGen file, frame-exact, so the drift is
  most likely the Avatar III photo-avatar engine. Compare the raw HeyGen render to confirm.
- Next: re-render W45 with the fixed voice text when credits allow, then upload.
- 2026-11-07 six-specialist review and ranked plan: `docs/REVIEW_2026-11-07.md`.
- W45 repair in progress: circle off, minimal face, re-voiced phrases and the Tencent correction
  (`reviewed/2026-W45/repairs.yaml`), on the existing render.

## Voice-first render — founder go-ahead 2026-11-07, measured the same day
- Speech (connector `create_speech`, voice clone): 20.6 s → 1 credit; 58.8 s → 3 credits ≈ **3 credits/min**,
  1 credit minimum per call. Word timestamps come back with the audio (no Whisper needed for timing).
- Avatar IV driven by our audio (`create_video_from_avatar` + `audioUrl`, photo look, 1080p): 20.6 s →
  **7 credits** ≈ 21/min (test video `ed4c026aba096782e42305365f197a08`).
- Per 9-min episode: narration ≈ 27 + face at open/sign-off only (~16 s) on Avatar IV ≈ 6 → **≈ 33 credits**,
  vs 63 for today's full Avatar III render, with better lip sync where the face shows.
- Repairs: batch every phrase into ONE speech call and cut it by the returned timestamps (`url#t=a,b`).
- **How to run it (built 2026-11-07, `pipeline/video/voicefirst.py`):**
  1. `output/<week>/voice_pack.md` (+ `.json`) comes with every script/score/polish/direct run, or run phase
     `voicepack` (it posts the pack on the review issue): ordered chunks `NN-face` / `NN-voice`; face chunks are the
     opening and sign-off, capped to `visuals.face_keep_seconds`; voice chunks ≤ `video.voicefirst.max_chars`.
  2. From chat (HeyGen connector): `create_speech` per chunk with the voice clone, text exactly as given (break tags
     kept); for face chunks also `create_video_from_avatar` with that `audioUrl`, Avatar IV, 1080p.
  3. Commit `reviewed/<week>/voice.yaml` (`<id>: {audio: <url>, duration: <s>, video: <url>}`; a voice chunk may be
     just its URL; ids must match the pack exactly), then run weekly-roundup phase `assemble`, this week: it joins
     the speech (0.25 s gaps) into `narration.wav`, builds `talking_head.mp4` with the face videos at their chunks
     (`face_spans.json`), and runs post-production with the face only on those spans.
- Founder decisions the same day: audience = enterprise leaders + broad audience + IT people/techies;
  repo stays public for now; music only if not licensed (we generate our own).

## English version: how to run (built 2026-11-07, `pipeline/scripting/translate.py`)
Same sources and shot plan as the Arabic week; only the words, voice, captions and on-screen text change.
A week folder ending in `-en` is English everywhere (`pipeline/language.py`): the English voice clone
`video.heygen.voice_id_en` (`e1412c88…`), Whisper in English, English pace (`words_per_minute_en`).
1. **translate** — weekly-roundup phase `translate`, week = the *Arabic* week (its script must be directed:
   run `direct` first if it has no shot markers). Writes `output/<week>-en/`: `script.md` (every marker kept in
   place and order — checked, one retry, else the phase fails), `plan.json` (English title / description /
   thumbnail), `items.json`, `critique.json` (one round, `config/critic_rubric_en.md`), `source_map.md`
   (gates assemble/import like the Arabic one), `heygen_paste.md`, `shotlist.md`; artifact `week-<week>-en`.
   Read `script.md` and `source_map.md` before going on; a hand-edited copy goes in `reviewed/<week>-en/script.md`.
2. **voicepack** — phase `voicepack`, week `<week>-en` → `voice_pack.md` with the English clone's id.
3. **From chat (HeyGen connector):** `create_speech` per chunk with the English clone; face chunks also
   `create_video_from_avatar` with that `audioUrl`; commit `reviewed/<week>-en/voice.yaml`.
4. **assemble** — phase `assemble`, week `<week>-en` → `talking_head.mp4`, then post (English captions).
5. **post** (re-run only if needed) → **preview** workflow with week `<week>-en`.
- Not covered for `-en` weeks: phases `script`, `polish` and `score` (they are the Arabic writer/critic);
  re-run `translate` instead. YouTube tags and hashtags in `publish` are still the Arabic ones.

## Earlier test week (2026-W43, folder `2026-W43-jo`)
- Approved script: `reviewed/2026-W43-jo/script.md` (one unsourced line removed by the founder).
- Paste pack for HeyGen: `reviewed/2026-W43-jo/heygen_paste.html` (5 scenes, copy buttons);
  the review issue #12 carries the same pack and the director's shot list (face 12 %, 75 shots).
- Next: founder renders the 5 scenes in HeyGen → run weekly-roundup with phase `import`, week
  `2026-W43-jo`, `video_url` = the HeyGen video ID or link → run the `preview` workflow.

## Built 2026-11-20 (founder: legal risk, account security, real photos)
- **Legal flags** (`pipeline/scripting/legal.py`): every source map gets a `legal.md`: allegations against
  someone on one weak outlet, buy/sell/invest imperatives, rulers/religion/state next to a negative claim, quotes
  without direct support. Shown on the Review issue; a render refuses while a major flag is unanswered in
  `reviewed/<week>/legal_ok.txt`. Flags, not legal advice. Breaking Shorts are not checked yet (no source map).
- **Security** (`docs/SECURITY.md`): `main` protected from force-push/deletion, every Action pinned to a commit,
  a daily channel-integrity check at 06:23 Gulf (`scripts/integrity.py`; baseline: 9 videos, @aithisweekme).
  The founder checklist in SECURITY.md (passkeys/Advanced Protection, managers, GitHub 2FA) is still open.
- **Visuals**: `[Visual: photo <subject>]` (licensed Wikimedia Commons photos, credited) and
  `[Visual: generated <scene>]` (own clips via reviewed/<week>/visuals.yaml; Higgsfield has 0 credits, so the
  founder makes them from the list in the Review issue). The shot list flags repeated stock and long digital runs.
  First used from W48.

## Open items for the founder
1. **Re-record avatar footage in landscape 16:9, mid-chest up** (the current avatar is portrait,
   so face shots show a narrow strip). Guide: `docs/recording_script.md`. Then update
   `video.heygen.avatar_id` in `config/settings.yaml`.
2. Render this week's episode in HeyGen (above).
3. Later: Google OAuth + YOUTUBE_REFRESH_TOKEN for publishing; X_BEARER_TOKEN (optional);
   native Ammani editor review (`docs/native_signoff.md`); decide whether the audience shifts
   from enterprise leaders to a broader Jordanian/Arab audience (planner prompt unchanged so far).

## HeyGen cost rules (audited 2026-10-26, Creator plan)
- Plan: Creator, $29/mo, 600 credits/month, renews on the 19th; unused credits roll over one cycle;
  no one-time top-ups on Creator (the only way to add credits is upgrading to Pro).
- **Motion engine is the cost driver.** Video look: Avatar III 4 credits/min, Avatar IV 31/min,
  Avatar V 48/min. AI Studio defaults to Avatar V, which is what made the October PDI videos cost
  ~48/min. Rule: one engine for the whole render (post-production cuts face and corner shots from the same
  presenter track, so engines cannot be mixed per shot). Avatar III by default, Avatar IV when the
  balance allows, never Avatar V. Layout Original, no background change.
- Avatar group default voice is now the Arabic clone `4c810d9c…` (it was the English clone).
  New AI Studio videos may open on another look, so pick the look named in `config/settings.yaml`
  (`video.heygen.look_name`) in every scene; the paste pack names it.
- Duplicate voice clones (`d6ee6521…` Arabic, `e1412c88…` and `9bc2309f…` English) are unused; left in place.
- Creative Studio on Creator: HeyGen Video model 0.24 credits/s (~14/min), renders the avatar in **16:9**
  (a landscape hero-shot workaround for the portrait avatar); images 2 credits each.
  Seedance, Veo, Wan, Gemini video models and Cinematic Shots are Pro only.
- Other rates (HeyGen help centre): Video Agent 80/min, translation 4–10/min, upscale 1–2 credits/s,
  Batch Mode / Video Podcast 3/min (whether the engine charge is added on top is unverified).
- Episode budget, ~8 min: all Avatar III ≈ 32 credits, all IV ≈ 250, all V ≈ 385.
  Monthly (~4.3 episodes): III ≈ 140–180 incl. hero shots and thumbnails (fits Creator);
  IV ≈ 1,070 (needs Pro above the 1,000 base tier).
- W43 next step: render on Avatar III (~32 of the 119 credits left) and judge the lip-sync quality.
- **Measured 2026-11-07, HeyGen connector (API-style render, not the web app):** W45, 5 scenes,
  8 min 57 s, photo look "Professional in blue shirt", Avatar III, 1080p → **63 credits
  (≈ 7 credits/min)**, nearly double the 4/min the web-app audit found. Budget connector renders
  at ~7/min; the web app may still be cheaper for the same engine.

## Ideas not built yet
- HeyGen's AI B-roll generator and Video Agent (web app only as far as known) for hero shots.
- Split-screen layout or tight crop for portrait footage, if re-recording is not possible.

## Useful commands
- Tests: `python -m pytest -q tests` (78 passing)
- Re-plan shots: weekly-roundup phase `direct`, week `<week>`
- HeyGen IDs: run the `heygen-assets` workflow
- Watchable copy of any week: run the `preview` workflow; the MP4 lands on branch `previews`

## Own-voice route (founder decision 2026-11-08)
The founder reads the script himself; no avatar, no lip-sync, no HeyGen credits.
1. Reading script: `reviewed/<week>/read_script.html` (phone-friendly; names written as said, no
   glosses or version numbers). W45's is ready.
2. He records the whole read as one audio file (phone is fine), optionally the opening and the
   sign-off as short landscape selfie videos, and shares links (Drive/Dropbox, anyone-with-link).
3. `reviewed/<week>/voice.yaml`: `narration: <link>` (+ optional `open:` / `close:` video links).
4. Run weekly-roundup phase `assemble`: talking head from his recording (selfie clips keep their own
   sound, so lips match; without them no face at all), then the normal edit. No speech repair runs on
   an own-voice recording.

### Script-guided edit (built 2026-11-12)
The own-voice edit now follows the approved script (`pipeline/video/guided.py`), so nobody lists stumbles by hand:
- a sentence said again → the later saying stays; doubled words and re-spoken names are cut;
- `pickups:` in voice.yaml = further files with sentences read again; each replaces its sentence in the main read;
- `narration:` may be a list of files read in order; `cut:` / `keep:` spans (first file's time) override the edit;
  `guided: false` switches it off.
- **How to run a recording:** commit the file(s) + `reviewed/<week>/voice.yaml` → weekly-roundup phase
  **`voicecheck`** (minutes: cleaned read + report, no video) → `preview` workflow with `what: voice` →
  `<week>-voice.mp3` and `<week>-voice.md` on the `previews` branch → founder listens → phase `assemble`.
- The report lists every cut and the script passages the recogniser did not find (check by ear; a real misread
  is fixed with a pickup). W45 check: all 7 hand-found stumbles found, plus a retake at 6:03 and a swapped
  «Blackwell Ultra / Vera Rubin» at 8:45.
- Speed: one recogniser pass (large-v3-turbo) per recording, cached by file; captions reuse its words (no second
  Whisper pass); card clips are reused between runs (`card_cache/`).
- English W45: the founder reads `reviewed/2026-W45-en/read_script.md`. Before `voicecheck`, make that text the
  week's script (commit it as `reviewed/2026-W45-en/script.md`, run `direct` for `2026-W45-en`): the edit follows
  `output/<week>/script.md`, and `translate` wrote a different wording there.
- `ANTHROPIC_API_KEY` replaced by the founder 2026-11-12 (translate passed).

## Founder decisions 2026-11-15 (host bio, wider region)
- **Host bio:** `publish.host_bio_en` goes under the chapters in every English description. Founder
  confirmed: "25 years", and name the large companies (Microsoft, Oracle, TIBCO), not all five. Channel About text: founder pastes it in YouTube Studio.
- **In the video:** one line about the host in the Welcome section. For W46 it goes in with
  Wednesday's revision (the Nvidia earnings line), so narration is regenerated once.
- **Wider region:** Egypt and North Africa, Turkey, Pakistan are now ingested (AI-narrowed searches in
  `ingestion.google_news_sites`) and the editor mentions them only when the news is major. No quota.
  **Superseded 2026-11-20 (founder):** Africa and Türkiye each get a seat when they have AI news (`scoring.min_per_region`).

## HeyGen on the Pro plan: measured costs and decisions (2026-11-16)
- Account reads plan `pro`. Measured: paid voice `heygen-voice-1` 1 credit for 58 s; one Nano Banana 2
  image 3 credits; 5 s image-to-video at 1080p 4 credits; talking face about 7 credits per 21 s.
- Cinematic Avatar (Seedance 2) with the grey-hoodie look failed ("reference file could not be
  downloaded"), not charged. Not retried; founder to decide.
- **Founder decision:** the face appears at the opening, the sign-off and for 6-8 s at each story
  change (about 35-45 credits an episode), not full length. First month keeps credits for tests.
- Own generated clips for a shot go in `reviewed/<week>/visuals.yaml` (see `visual_assets.own_clips`).
- **Founder 2026-11-16:** narrate W46 on the paid voice model `heygen-voice-1` (about 10 credits an
  episode); up to about 50 credits of generated clips for W46's key shots. Cinematic Avatar failed
  with the blue-shirt look too (same "reference file" error, not charged): parked.

## Daily comment inbox (built 2026-11-16)
`inbox` workflow, daily 05:13 UTC: `pipeline/publish/inbox.py`, `scripts/inbox.py`, state in `data/inbox.json`.
YouTube and Instagram are read and answered (after the founder's `approve` on the Inbox issue); LinkedIn and
TikTok cannot be read by an app and are listed to check by hand. Likes are never automatic (no API). See
`docs/SOCIAL.md`. Open: founder to create the LinkedIn, Instagram and TikTok apps, in that order.
- **Brand (founder 2026-11-16):** the official logo and banner are the ones live on the YouTube channel
  (`assets/brand/channel_logo_800.jpg`, `channel_banner_2560x1440.png`; gold "AI THIS WEEK" in a ring). The
  generated bars logo (`logo_800.png`) and four symbol concepts were rejected. Use the channel logo on every platform.
- **Brand settled (founder 2026-11-16, option 2 of the last round):** royal violet, white and gold, Sora
  lettering. Source of truth `config/brand.md`. Cards, overlays, thumbnail, end card, Shorts cards and the
  English sting use it; `assets/brand/` has the new logo, YouTube banner and LinkedIn banner for the founder
  to upload. The earlier channel logo and banner are in `assets/brand/previous/`.
- **Presenter look (founder 2026-11-16):** look C, navy blazer over a white t-shirt in a bright studio with a
  violet glow (`assets/brand/presenter/look_c_navy_blazer.png`), wide format, replaces the grey hoodie. Made
  from the original avatar photo: the dark-studio looks A and B made him look older and were rejected.
  Rendered with `create_video_from_image` (the still, not a saved HeyGen look).
  Skin warmed on 2026-11-16 (the first render looked pale); founder approved the look for the W46 edit.
  For W46: render face chunks with `create_video_from_image` from this still, wide format, no side layout.

## Founder notes for future videos (2026-11-17)
- **Presenter look:** his shoulders are wider than the navy-blazer photo shows. Regenerate the look with
  broader shoulders (a more solid build), then re-test a speaking clip before any episode uses it.
- **Hand gestures:** some presenter clips should show hand gestures. The current look is cropped at the
  chest; this needs a wider framing (waist up) and a gesture-capable render. Needs a HeyGen credit test
  the founder approves first.
- **Clip endings:** the last moment of some presenter clips looks artificial. Trim the tail of each face
  clip (or ask for a longer clip and cut early) and check every clip's last second in the preview.
- **Shorts need a proper review before any go out:** listen to each one, not only look. W46-en faults:
  dead silence at the script's pauses, an opening that started on the episode's hand-over sentence.

- **Presenter look D approved (founder, 2026-11-17):** `assets/brand/presenter/look_d_navy_blazer_hands.png`, the
  hands-visible body with the original look C face pasted back unchanged (the AI edit had altered the face; the first
  file under this name was rejected). Use from W47. The face must never be regenerated: body edits only, face copied
  from look C. Still to do: a speaking test with this still, hand gestures now and then, natural clip endings.

- **Channel artwork (founder, 2026-11-17):** emblem logo `assets/brand/logo_800.png`; banners with the navy-blazer
  portrait in the emblem ring (`youtube_banner_2560x1440.png`, `linkedin_banner_2256x382.png`), built by
  `scripts/brand_banners.py <out dir> <portrait>`. The hoodie banner and the plain set are under `assets/brand/previous/`.
  YouTube banner is set by the `brand` workflow; profile pictures and the other channels are manual (no API).

- **W46-en is edited and checked, waiting for the founder's go-ahead to publish (2026-11-18).** Final run 44199645547:
  10:39, 4K master, three Shorts, thumbnail with the approved portrait. Title A and description from
  `reviewed/2026-W46-en/meta.yaml`. 15 of our own clips (`visuals.yaml`), 12 stock clips blocked by id. The Jensen Huang
  passage was corrected against Al Jazeera and TechCrunch (`sources_ok.txt`). After upload: set each Short's "related
  video" link to the episode in YouTube Studio (needs Advanced features; no API).

## Weekly timing (founder 2026-11-18)
The scheduled script run is **Friday 06:00 UTC (10:00 Gulf)**, moved from Saturday for a full day of slack.
Friday: script → founder review. Saturday: English, voice, render, upload (private/scheduled). Sunday 17:00 Gulf: public
(founder 2026-11-24: kept after weighing 07:00 and 15:00).
The chain (2026-11-19): reply `approve` on the week's Review issue → English version → voice, render, Shorts →
previews + a "ready" comment (and WhatsApp alert when set) → reply `publish` → unlisted upload, public at the
Sunday slot via the release gate → LinkedIn and Facebook episode posts (phase `announce`) once it is public.

## Handoff — 2026-11-19 (for a session on the founder's computer with the Chrome extension)
Working and automatic: news watch → breaking Shorts (approve with `post <week>` on the Breaking Shorts issue);
weekly script Fridays 10:00 Gulf → `approve` → render → `publish` → Sunday 17:00 Gulf → LinkedIn/Facebook at release;
Monday report with watch time and where viewers leave; daily comment inbox (now incl. held-for-review comments).
Open founder items, best done in the browser:
1. ~~YouTube Studio → Comments → Held for review~~: checked 2026-11-19, none held. The daily inbox now reads held comments.
2. ~~WhatsApp Channel "AI This Week"~~: created 2026-11-19, link set in `social.whatsapp_channel_url`.
3. Partnerships Gmail: `aithisweek.partnerships@gmail.com` created with forwarding to the founder (2026-11-19) and set in
   `publish.partnerships_email`. Line added to all 8 existing videos (run 44547065294, re-check 0 left). Media kit: `docs/media_kit.html`
   (private artifact https://claude.ai/artifact/DvpDDA8RBojD9JdU8ohkmR; founder approved 2026-11-19; numbers on request).
4. Meta (2026-11-19): Facebook Page "AI This Week" (profile.php?id=61596963440255; logo, cover, bio, YouTube link,
   partnerships email) and Instagram @aithisweekme (Creator) are made and linked. Blocked: the Meta for Developers
   sign-up needs phone verification and SMS codes to the founder's UAE number never arrive; Accounts Center now refuses
   the number ("try a different phone number"), likely a rate limit. Retry after a day, or verify with a card (founder
   enters it). Then: Business app, both products, redirect URI, secrets, `connect` (docs/SOCIAL.md, last section).
5. ~~TikTok~~ (2026-11-19): @aithisweek switched from a private to a public account (it was private, which is why
   "Everyone" was never offered); 6 Shorts set to Public (Jensen Huang was still in TikTok's content review).
   The duplicate ADNOC/G42 post from 17 Nov 9:19 pm stays private. Bio set (80-char limit): "AI news for the Middle
   East, every Sunday 17:00 Gulf time. Not financial advice." Display name "AI This Week" live (checked 2026-11-20);
   all 6 Shorts public incl. Jensen Huang (review cleared). Watch whether the next
   automatic post lands public now, or still private because the TikTok app is unaudited.

## Languages on YouTube (checked in Studio 2026-11-19)
- **Auto-dubbing is not available on this channel yet:** no setting under Settings → Upload defaults → Advanced, and
  no automatic dub appears on any video's Languages page (press reports say it reached all creators in Feb 2026;
  not so for this channel today). Re-check monthly.
- **Our own audio tracks ARE available:** Languages → Add language → Arabic → Audio → "Select File" (Studio only;
  YouTube's note: the track cannot be trimmed there and "should roughly align to the length of your video"). This is
  the route for an Arabic track in the founder's cloned voice on the English episode (one video, one view count).
- Per-language title, description, thumbnail and manual subtitles can be added in the same panel. English
  episodes now carry an Arabic title/description too (2026-11-20, `description._arabic_localization`): the Arabic
  plan's own title, hook and headlines, the sources and the Arabic disclaimer. Off switch: `publish.localizations: false`.

## Connected tools worth using (reviewed 2026-11-19, none adopted yet)
- **HeyGen video translation** (connector `create_video_translation`): verified on the current plan: Arabic (Jordan)
  and other Arabic dialects, Turkish, Urdu (Pakistan). Voice clone + lip-sync, or `translateAudioOnly` = just a dubbed
  track to add in Studio → Languages → Arabic → Audio. Cost unverified (help-centre figure ~4–10 credits/min).
  Next step when wanted: a 1-minute Arabic (Jordan) test on the NVIDIA episode (`startTime`/`endTime`).
- **Higgsfield TikTok publish** (`tiktok_prepare_publish`): public or draft posts from a verified source; needs a
  Higgsfield-hosted file and the founder's approval in a form each time, so manual only.
- **Bigdata.com monitors** (named-company news events), **Crustdata** (sponsor prospecting in MENA AI/cloud),
  **TinyFish monitors** (regulator/ministry page watchers), **Higgsfield virality predictor** (Short pre-check).
- Plugins offered: TubeAlfred (channel/SEO audits, comment leads), Arcmira (sponsor research on similar shows).

## Channel dashboard (2026-11-20)
- Page: https://claude.ai/artifact/DYVLTuaQmaQZcFALvYdwuP (private, Claude "Data" type). Pipeline map:
  https://claude.ai/artifact/2GKj3BCvWrB3UKsoHKYKj2 (source `docs/pipeline_map.html`).
- Numbers: `scripts/channel.py report` writes `data/dashboard/*.csv` via `pipeline/publish/dashboard.py` (tested in
  `tests/test_dashboard.py`); the channel workflow commits them, on manual runs too. Account states and notes that no
  API gives are in `dashboard.ACCOUNTS`: edit there when an account changes (e.g. Instagram/Facebook unblocked).
- Sections (2026-11-20): needs you, YouTube cards, monetisation tracker (12-month watch hours vs 8,000, projected
  date from the last four weeks), week-by-week history, views by video (with Short origin), retention curve with
  chapters, audience by country and traffic source, channels, TikTok, pipeline health.
- Refresh: local scheduled task `ai-this-week-dashboard-refresh` (Mondays ~10:17 Gulf, Auto mode, runs only while the
  Claude app is open; if closed it runs on next launch) uploads the eleven files and repoints the datasets. TikTok Shorts
  (`tiktok_videos`) is a 20 Nov copy the task does not refresh: the TikTok app cannot read view counts.

## TikTok posting (2026-11-20)
An unaudited TikTok app may post only to private accounts, and @aithisweek is public. TikTok's app review would
likely be refused (it wants apps for many creators, with a full posting screen: no default privacy, unticked
interaction switches, consent line, preview), so `social.tiktok_mode: inbox` sends each Short to the founder's
TikTok drafts instead (`TikTok.post_video(mode="inbox")`). The Breaking Shorts issue shows the caption to paste;
in the TikTok app: tap the inbox notification, turn on the AI-generated label, paste, Post. Limit: 5 pending drafts
a day. Not yet confirmed on a real Short that drafts work for an unaudited app on a public account; if the next
one fails, upload by hand in TikTok Studio (done for the Anthropic IPO Short, 20 Nov).


## Story ranking (built 2026-11-22, for W48; plan `docs/plans/2026-11-22-news-ranking.md`)
The weekly job now stops after ranking the week's stories and waits for the founder before it writes the script.
- **Flow:** Friday job → ingest → `rank` → `data/ranking/<week>.json` committed → issue **"Ranking: <week>"** with
  every story's scores, reasons, gates and slot → the founder comments `/story <id> deep because <reason>` (or
  `quick`, `radar`, `short`, `drop`, `auto`; a story's number works in place of the id) as needed, then `approve` → the script job runs from the
  approved slots → the usual "Review: …" issue.
- **What is in code, not in the model:** the weights (decision ×3, regional consequence ×2, evidence ×1,
  tension ×1, max 21), the four gates, the named-actor test, the slots (3 deep, flex 2–4; 3 quick; 3 radar; the
  Africa and Türkiye seats), the Shorts picks, the order of the plan's segments.
- **Model:** Claude Haiku 5.5 for the 0–3 scores and reasons (`ranking.model`). No API key → keyword fallback,
  labelled on every story it judged.
- **Settings:** `config/settings.yaml` → `ranking:`. `require_approval: false` restores the old one-step run.
- **Locally:** `python run_pipeline.py rank --week <week>` writes `output/<week>/ranking.md`.
- **Shorts candidates are listed, not yet made:** the ranking names up to three (breaking context, evergreen
  explainer, best moment) with their fact, implication and question. Making an explainer Short from a candidate
  is not built; breaking Shorts still come from the news watch (`pipeline/breaking.py`).
- **Dry run on 2026-W47 (2026-11-22, keyword fallback, no API key on the Mac):** 3,431 scored items → 20 stories.
  Deep: SDAIA's AI year in Saudi universities (18/21), the NSA outage at a Middle East facility (18), Anthropic's
  Wall Street debut (16). Quick: MGX and the Anthropic IPO (17), a Claude Code release (15), an African-markets
  piece (Africa seat). The Haiku judge has not run on live data yet: the first W48 run is its first real test.
- **Second round, 2026-11-23, from that dry run (PR after #62):**
  - Three rules in code, for either judge: a headline made only of general words ("Artificial Intelligence") is
    not a story; a buy-or-sell headline is on the kill list and never reaches the radar or the Shorts; a routine
    version release fails the depth gate and never reaches the radar. `/story <id> radar because …` overrides.
  - A story's own article is always first among its articles. It had been pushed out by higher-tier outlets,
    so the MGX story's link and its named-actor test both read another article (17/21 then, 21/21 now).
  - The Ranking issue opens with **Before you approve** (rough-scores warning, stories that outscored one in the
    episode, stories that turn on the same company, seats), then the episode in running order with a link, the
    scores and the model's reasons per story and the run time of the deep and quick slots, then the commands.
    The full score table and every reason are folded at the bottom.
  - W47 again, keyword fallback: deep MGX and the Anthropic IPO (21), Microsoft's outage warning (17), Anthropic's
    Wall Street debut (16); quick the Riemann claim (16), the Africa seat (11), the Türkiye seat (8).
- **Known limits:** with the keyword fallback one event under two headlines is only pointed at, not joined (W47:
  MGX and the debut); the Türkiye seat's region comes from the outlet, not the story.
- **Ease of use, 2026-11-23 (third round):** every story has a number and commands take it
  (`/story 7 quick because …`); several commands fit in one comment and numbers mean the list as shown; plain
  `approve` works. The issue opens with a verdict line ("Ready to approve" or "N things to look at") and the run
  time against `scripting.target_minutes`. After a command the bot replies with what moved and replaces the
  issue's body, so the issue is always one current list. Flags are grouped, commands sit in copyable blocks,
  scores show as strips (numbers stay in the folded table), the judge's one-sentence `summary` leads each story
  with the headline as the link, and the left-out list shows its five highest. Not yet run on GitHub.

## Where a release goes (checked 2026-11-23; table in `docs/SOCIAL.md`)
- The reply to `publish` now lists, per platform, what happens to the episode and to the Shorts, from
  `pipeline/publish/release_status.py`. Not yet seen on GitHub: its first real run is the next `publish`.
- **For the founder:** WhatsApp alerts are off until `WHATSAPP_PHONE` and `CALLMEBOT_APIKEY` are set. Facebook
  gets the episode as a link post and no Reel has posted there. Instagram has posted one Reel; the rest were
  skipped and the cause is not investigated. W45-en Shorts #2 and #3 still wait for approval.
- **Decided by the founder, 2026-11-23:** Instagram and TikTok captions stay without the WhatsApp link (he
  adds it to the two bios by hand); weekly Shorts stay off and the two W45 entries were marked skipped; a region
  seat takes a quick slot only from 11/21 up, a weaker one gets a radar line.
- **WhatsApp (founder 2026-11-28):** the WhatsApp Channel is no longer promoted and its link left the captions;
  captions point to Instagram and TikTok instead (`social.follow`). WhatsApp stays only for the founder's own
  status, by hand from the "WhatsApp kit" issue. WhatsApp alerts are dropped (CallMeBot was full).
