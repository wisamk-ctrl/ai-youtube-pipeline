# CLAUDE.md — ai-youtube-pipeline

Weekly Arabic AI-news YouTube show, «أسبوع الذكاء الاصطناعي», presented by Wissam's digital twin.

## Channel standards (founder decisions — follow them in every change)
- **Language:** Jordanian colloquial Arabic (urban Ammani), never formal MSA. Source of truth:
  `config/style_guide.md`; the critic rubric (`config/critic_rubric.md`) enforces it.
- **Look:** premium explainer, not a talking head. Face on screen 20–30 % of runtime, visuals
  (source cards, number cards, title cards, stock footage) for the rest. Source of truth:
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
- `python run_pipeline.py <phase> --week <week>` (phases: ingest script polish score video import post publish all)
