# Visual standard — «أسبوع الذكاء الاصطناعي»

Founder decision, 2026-10-25: the channel looks like a premium YouTube explainer, not a
talking head. The presenter's face earns trust in short appearances; pictures carry the story.
This file is the single source of truth. The director pass reads it on every run and the
shot-list check enforces its numbers. Change it here only.

## Screen time
- **Face on screen 20–30 % of the runtime**, never more than 35 %.
- **No face stretch longer than 20 seconds.** No single visual shot longer than 12 seconds:
  a long passage gets several visuals in a row.
- After two visuals in a row, the next one may be a **corner shot**: the visual full screen
  with the presenter in a small circle, so they stay present without filling the frame.

## When the face is on screen
- The cold open's first sentence, and the greeting.
- The first sentence of each story (the presenter introduces it).
- Every «ليش بيهمّنا؟» answer: the regional angle is the presenter's own voice.
- Reactions, questions to the viewer, and the outro.

## When a visual is on screen
- **Every story shows its source** at least once: a clean news-clipping card with the
  publisher, the headline and the date. It is the on-screen attribution; never skip it.
- **Every important figure gets a number card**: the figure counting up, an Arabic label.
- **A concept or a chapter gets a title card**: a short Arabic phrase, large and calm.
- **Generic context gets stock footage**: data centres, chips, offices, cities, hands on
  keyboards. Search terms in English, concrete and filmable.

## Never
- Clips from other companies' keynotes, other YouTube channels, films or TV: copyright risk.
- Stock shots that pretend to show a specific real person, product or event.
- Logos animated or altered; text-heavy visuals the viewer cannot read in two seconds.
- A visual that contradicts or adds to what the narration says.

## Shot markers (written by the director pass, never spoken)
- `[Face]` — full-frame presenter from this sentence on.
- `[Visual: source <item id>]` — the news-clipping card for that source item.
- `[Visual: number <figure> | <Arabic label>]` — e.g. `[Visual: number 80% | من الأسئلة بتنحلّ بدون مهندس]`.
- `[Visual: title <short Arabic phrase>]` — e.g. `[Visual: title نافذة السياق]`.
- `[Visual: stock <English search terms>]` — e.g. `[Visual: stock server racks in a data centre, blue light]`.
- `[Corner: <same forms as Visual>]` — that visual with the presenter in the corner circle.
Each marker sits on its own line directly before the sentence where the shot starts. A shot
lasts until the next shot marker.

## Fallbacks (the episode never fails for want of a picture)
- Stock footage comes from Pixabay (Pexels if configured instead). No key, or no result:
  the shot becomes a branded motion backdrop (navy, gold lines, no text), never a face shot,
  so the face share stays on target.
- An asset that fails to render: the shot becomes a face shot.
- A source id that is not in the week's items: the shot becomes a title card with the
  section title.
- Stock credits (photographer and link) are saved with the episode for the description.
