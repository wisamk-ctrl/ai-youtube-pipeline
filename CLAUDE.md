# CLAUDE.md — ai-youtube-pipeline

Weekly Arabic AI-news YouTube show, «أسبوع الذكاء الاصطناعي», presented by Wissam's digital twin.

## Channel standards (founder decisions — follow them in every change)
- **Language:** Jordanian colloquial Arabic (urban Ammani), never formal MSA. Source of truth:
  `config/style_guide.md`; the critic rubric (`config/critic_rubric.md`) enforces it.
- **Look:** premium explainer, not a talking head. Face full-frame only 10–20 % of runtime
  (presence through corner shots instead); tech/AI/computer animation is the house look
  (Pixabay animations, generated tech motion, source/number/title cards). Source of truth:
  `config/visual_standard.md`; the director pass and the shot-list check enforce it.
- **Facts:** every claim traces to a source item; `source_map.md` lists any that do not.
- **Never** prescribe investments, never invent figures, never use third-party video clips.

## Render routes
- Automatic: phase `video` (needs HeyGen API credits).
- Manual (current default): the review issue's paste pack → HeyGen web app → phase `import`
  with the video's ID or link → post-production runs automatically.
- Presenter avatar and voice IDs live in `config/settings.yaml` under `video.heygen`.

## Commands
- `python -m pytest -q tests`
- `python run_pipeline.py <phase> --week <week>` (phases: ingest script polish score direct video import post publish all)
- Secrets: ANTHROPIC_API_KEY, YOUTUBE_API_KEY, HEYGEN_API_KEY, PIXABAY_API_KEY (stock footage), Google OAuth for publishing.
