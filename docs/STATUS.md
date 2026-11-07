# Status and handoff — 2026-10-26

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

## Earlier test week (2026-W43, folder `2026-W43-jo`)
- Approved script: `reviewed/2026-W43-jo/script.md` (one unsourced line removed by the founder).
- Paste pack for HeyGen: `reviewed/2026-W43-jo/heygen_paste.html` (5 scenes, copy buttons);
  the review issue #12 carries the same pack and the director's shot list (face 12 %, 75 shots).
- Next: founder renders the 5 scenes in HeyGen → run weekly-roundup with phase `import`, week
  `2026-W43-jo`, `video_url` = the HeyGen video ID or link → run the `preview` workflow.

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
