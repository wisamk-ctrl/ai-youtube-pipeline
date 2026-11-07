# Visual standard — «أسبوع الذكاء الاصطناعي»

Founder decision, 2026-10-25, tightened 2026-10-26 ("less of my face, more animation about
tech, AI and computers"): the channel looks like a premium YouTube explainer, not a talking head. The presenter's face earns trust in short appearances; pictures carry the story.
This file is the single source of truth. The director pass reads it on every run and the
shot-list check enforces its numbers. Change it here only.

## Screen time (minimal-face mode — founder, 2026-11-07)
- **The face is on screen only at the open and at the sign-off** (`visuals.face_mode: minimal`,
  up to `face_keep_seconds`, 8 s, at each end). Lip sync is visible on a full-frame face, so the
  face is kept to where it earns trust: the greeting and the goodbye. Everywhere else a visual is
  on screen with the presenter's voice over it.
- The old 10–20 % face share (`visuals.face_share`) applies only when `face_mode` is `normal`.
- **No single visual shot longer than 12 seconds**: a long passage gets several visuals in a row.
- **Corner circle is OFF** (founder, 2026-11-07: it looked wrong). `visuals.corner.enabled: false`
  renders every `[Corner: …]` as a full-screen visual with the voice over it. The markers stay in
  the scripts so a better presence layout can be switched on later without redirecting.

## When the face is on screen (full frame)
- The cold open's first sentence, and the greeting.
- The sign-off.
- Nowhere else: a `[Face]` marker mid-episode becomes a visual from the house stock queries.

## The presenter's presence elsewhere
- The voice carries the presence. The first sentence of each story and every «ليش بيهمّنا؟» answer
  are the presenter's voice over a visual (the `[Corner: …]` markers, rendered full-screen).

## Sound and the sting
- The intro sting (`assets/intro_sting.mp4`, our own code-rendered sting) plays after the cold open.
- A music bed we synthesise ourselves (never licensed third-party music) sits ~24 dB under the voice
  and ducks under it; a soft synthesised whoosh marks each section cut. The master is −14 LUFS.

## Captions and lower-thirds
- Captions: bottom-centre, ~54 px at 1080p, in a translucent navy box; Latin runs are kept intact.
- Lower-thirds sit at 28 % from the bottom, clear of two-line captions.

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
- `[Corner: <same forms as Visual>]` — that visual with the presenter in the corner circle (full-screen while the circle is off).
Each marker sits on its own line directly before the sentence where the shot starts. A shot
lasts until the next shot marker.

## Fallbacks (the episode never fails for want of a picture)
- Stock footage comes from Pixabay (Pexels if configured instead). A hit must share a tag with
  the query and carry no off-brand subject (people, food, animals, nature, fantasy) the query did not
  ask for; among relevant hits the most relevant wins, animation first on a tie. No key, or no result: the shot becomes a generated tech animation
  (a moving network of nodes in the brand colours, no text), never a face shot.
- An asset that fails to render: the shot becomes a face shot.
- A source id that is not in the week's items: the shot becomes a title card with the
  section title.
- Stock credits (photographer and link) are saved with the episode for the description.
