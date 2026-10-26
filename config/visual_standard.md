# Visual standard — «أسبوع الذكاء الاصطناعي»

Founder decision, 2026-10-25, tightened 2026-10-26 ("less of my face, more animation about
tech, AI and computers"): the channel looks like a premium YouTube explainer, not a talking head. The presenter's face earns trust in short appearances; pictures carry the story.
This file is the single source of truth. The director pass reads it on every run and the
shot-list check enforces its numbers. Change it here only.

## Screen time
- **Face on screen 10–20 % of the runtime**, never more than 25 %.
- **No face stretch longer than 12 seconds.** No single visual shot longer than 12 seconds:
  a long passage gets several visuals in a row.
- The presenter stays present through **corner shots** (the visual full screen, the presenter
  in a small circle) rather than full-frame face shots.

## When the face is on screen (full frame)
- The cold open's first sentence, and the greeting.
- The outro.
- At most one short reaction or question to the viewer per story.

## When the presenter is in the corner
- The first sentence of each story (the presenter introduces it over its first visual).
- Every «ليش بيهمّنا؟» answer: the regional angle is the presenter's voice, over a visual.

## When a visual is on screen
- **Tech, AI and computer animation is the house look.** Abstract and animated: neural
  networks, glowing data streams, circuit boards, code on screens, servers and data centres,
  digital globes and network maps, chips under light. Prefer animation over live footage.
- **Every story shows its source** at least once: a clean news-clipping card with the
  publisher, the headline and the date. It is the on-screen attribution; never skip it.
- **Every important figure gets a number card**: the figure counting up, an Arabic label.
- **A concept or a chapter gets a title card**: a short Arabic phrase, large and calm.
- **Stock search terms** are English, concrete and visual, and lean to animation:
  "neural network animation", "digital data flow", "circuit board macro", "code on screen".

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
- Stock footage comes from Pixabay, animations first, then live footage (Pexels if
  configured instead). No key, or no result: the shot becomes a generated tech animation
  (a moving network of nodes in the brand colours, no text), never a face shot.
- An asset that fails to render: the shot becomes a face shot.
- A source id that is not in the week's items: the shot becomes a title card with the
  section title.
- Stock credits (photographer and link) are saved with the episode for the description.
