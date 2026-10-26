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
- **Presenter:** HeyGen avatar `dd64d6001c4e41c5a91b2fb9eead42a6` ("Sam -- 1") and Jordanian voice
  clone `4c810d9c9906445f81dfd4f7d32259e0`, both in `config/settings.yaml`.
- **Secrets on the repo:** ANTHROPIC_API_KEY, YOUTUBE_API_KEY, HEYGEN_API_KEY, PIXABAY_API_KEY.
- **Render route:** manual (HeyGen web app on the monthly plan; API credits not bought).

## This week (2026-W43, folder `2026-W43-jo`)
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

## Ideas not built yet
- HeyGen's AI B-roll generator and Video Agent (web app only as far as known) for hero shots.
- Split-screen layout or tight crop for portrait footage, if re-recording is not possible.

## Useful commands
- Tests: `python -m pytest -q tests` (78 passing)
- Re-plan shots: weekly-roundup phase `direct`, week `<week>`
- HeyGen IDs: run the `heygen-assets` workflow
- Watchable copy of any week: run the `preview` workflow; the MP4 lands on branch `previews`
