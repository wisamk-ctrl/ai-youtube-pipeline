# CLAUDE.md — ai-youtube-pipeline

Weekly Arabic AI-news YouTube show, «أسبوع الذكاء الاصطناعي», presented by Wissam's digital twin.

## Channel standards (founder decisions — follow them in every change)
- **Language:** Jordanian colloquial Arabic (urban Ammani), never formal MSA. Source of truth:
  `config/style_guide.md`; the critic rubric (`config/critic_rubric.md`) enforces it.
- **Look:** premium explainer, not a talking head. Face only at the open and the sign-off
  (`visuals.face_mode: minimal`, 2026-11-07, because of the avatar's lip sync); no corner circle;
  tech/AI/computer animation is the house look (Pixabay animations, generated tech motion,
  source/number/title cards); our own generated music only, never licensed. Source of truth:
  `config/visual_standard.md`; the director pass and the shot-list check enforce it.
- **Facts:** every claim traces to a source item; `source_map.md` lists any that do not.
- **Never** prescribe investments, never invent figures, never use third-party video clips.

## Current state
Read `docs/STATUS.md` first: what is done, this week's episode, and the founder's open items.
Then `docs/LESSONS.md`: every past run's faults and where each fix is enforced — apply them, and add
to it whenever a run teaches something (script lessons also go in `config/lessons_editorial.md`,
which the writer, reviewer and critic read on every run).

## Render routes
- **Voice-first (default):** `voice_pack.md` (phase `voicepack`, also written by script/direct) → speech per chunk
  + Avatar IV only for the face chunks via the HeyGen connector → `reviewed/<week>/voice.yaml` → phase `assemble`.
- Automatic: phase `video` (needs HeyGen API credits).
- Manual: the review issue's paste pack → HeyGen web app → phase `import`
  with the video's ID or link → post-production runs automatically.
- Presenter avatar and voice IDs live in `config/settings.yaml` under `video.heygen`.

## Commands
- `python -m pytest -q tests`
- `python run_pipeline.py <phase> --week <week>` (phases: ingest script polish score direct video import post voicepack assemble publish all)
- Secrets: ANTHROPIC_API_KEY, YOUTUBE_API_KEY, HEYGEN_API_KEY, PIXABAY_API_KEY (stock footage), Google OAuth for publishing.
