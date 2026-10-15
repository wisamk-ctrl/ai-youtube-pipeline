# AI YouTube Pipeline: weekly Arabic AI-news roundup

An automated pipeline that turns a week of AI news into an 8-minute Modern Standard Arabic
script and a talking-head MP4 of your digital twin (your cloned face and voice).

```
RSS newsletters ─┐
                 ├─► Phase 1: ingest → score → filter ─► Phase 2: Claude prompt chain ─► Phase 3: HeyGen
X API v2 top-10 ─┘     items.json                          plan.json + script.md          (or ElevenLabs + D-ID)
                                                            ▲ human review gate            talking_head.mp4
```

## Directory structure

```
ai-youtube-pipeline/
├── README.md
├── requirements.txt
├── .env.example                    # secrets template; copy to .env (gitignored)
├── .gitignore
├── config/
│   └── settings.yaml               # feeds, X accounts, scoring, script length, video provider
├── run_pipeline.py                 # CLI orchestrator: ingest | script | video | all
├── pipeline/
│   ├── config.py                   # settings + env loading
│   ├── models.py                   # NewsItem, the object passed between phases
│   ├── script_format.py            # marker parsing: spoken text, TTS text, cue sheet, chunking
│   ├── ingestion/                  # ── Phase 1
│   │   ├── rss_ingest.py           #   newsletter RSS aggregation
│   │   ├── x_ingest.py             #   X API v2: top 10 posts of the week from curated accounts
│   │   ├── scoring.py              #   enterprise/regional relevance scoring, noise filter, dedupe
│   │   ├── text_utils.py
│   │   └── engine.py
│   ├── scripting/                  # ── Phase 2
│   │   ├── prompts.py              #   editor → writer → reviewer prompts, marker vocabulary
│   │   └── script_engine.py        #   Anthropic API chain (structured plan, streamed Arabic script)
│   └── video/                      # ── Phase 3
│       ├── common.py               #   retrying HTTP, polling, streamed download
│       ├── heygen_client.py        #   Option A: HeyGen avatar + voice
│       ├── elevenlabs_did_client.py#   Option B: ElevenLabs voice → D-ID presenter
│       └── engine.py
└── tests/
    └── test_offline.py             # no network or keys needed
```

## Setup

```bash
cd ai-youtube-pipeline
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env               # then fill in the keys and your avatar/voice IDs
pytest -q                          # offline tests
```

## Running on your Mac (Ollama)

```bash
make setup            # .venv + dependencies
make ollama-check     # Ollama up? which models? does the configured one answer JSON?
make extract-test     # tag the sample week with the local model and score it (no API key)
make weekly           # this week's ingest + radar + script
make install-launchd  # every Saturday 10:00 local time; log in output/launchd.log
```

## Weekly run

```bash
python run_pipeline.py all                         # ingest + script, then stops for review
# read / edit output/<week>/script.md
python run_pipeline.py video --dry-run             # inspect tts_text.txt and cue_sheet.json (free)
python run_pipeline.py video                       # paid render → output/<week>/talking_head.mp4
python run_pipeline.py post --shorts "12-55,180-240"   # optional: Arabic captions + 9:16 Shorts (local, free)
```

Schedule it with cron (for example, Saturday 06:00): `0 6 * * 6 cd /path/ai-youtube-pipeline && .venv/bin/python run_pipeline.py all`.
If the process dies while a render is in progress, re-attach without paying for a second render:
`python run_pipeline.py video --resume-video-id "$(cat output/<week>/talking_head.job.txt)"`.

## How each phase works

**Phase 1: ingestion.** Feeds are fetched with timeouts, and one broken feed never stops the run.
X posts come from the official API, with replies and reposts excluded. Posts are ranked by weighted
engagement and the top 10 are kept. Every item then gets a transparent score:
`(enterprise keywords + GCC/MENA bonus + log engagement + recency) × source weight − noise penalty`.
Items below `min_score` are dropped and near-duplicates are merged. `items.json` keeps the
per-item `score_breakdown`, so you can see why a story was kept or dropped and tune the keyword
tables in `scoring.py`.

**Watchlist (`config/watchlist.yaml`).** The names we follow on purpose, in three tracks — models
(US / Europe / China / Gulf), agents, chips & inference — each with aliases, its Arabic name, official
feeds, GitHub repo and Hugging Face org. Station 1 adds a Google News search per name, the official
feeds, GitHub releases and new Hugging Face models (all free), and tags every item with the names it
mentions, so scoring can reserve seats per track (`scoring.min_per_track`) and the editor can build
the fixed episode shape: models → agents → chips → radar. Gulf names carry a 1.3× weight.

**Radar (`pipeline/radar/`).** Names that are *not* on the watchlist. A model reads every collected item once and
extracts the organisations, models and products it is about (cached per item). `radar.extraction.provider`
picks `ollama` (a local model via `/api/chat` with a JSON-schema `format`, free; set `ollama_model` from
`ollama list`) or `anthropic` (Haiku 5.5, ≈$0.05/week); hard signals come from Hugging Face trending, OpenRouter's new models, fast-growing GitHub
repos and Hacker News. A name becomes radar news when ≥ 2 independent sources make it their subject
and ≥ 1 hard signal backs it (`radar.min_sources` / `min_signals`). The weekly issue carries the
candidate table (`radar_report.md`); `data/radar_state.json` remembers every name (committed back by
the workflow). Promote a name by adding it to the watchlist; silence one by setting `status: ignored`.

**Deciding (Phase C).** The weekly review issue carries the radar table and a coverage report (items
per track and region; watched names with no news in 4 weeks). Reply `/promote <name> --track … --group …
--ar …` or `/ignore <name>` on the issue: `radar-decide.yml` opens a pull request that adds the name to
`watchlist.yaml` (promote) or commits the ignore. The same script runs locally: `python scripts/radar_decide.py list|promote|ignore`.

**Phase 2: scripting (Claude).** This phase is a chain of three calls, each doing one job:
1. **Editor.** `messages.parse` returns a validated Pydantic `EditorialPlan`: 5–7 stories,
   their order, the enterprise angle and B-roll ideas. Item IDs that don't exist are removed.
2. **Writer.** A streamed call writes the full MSA script with `[Pause]`, `[Show B-Roll: …]`,
   `[On-Screen Text: …]` and `[Section: …]` markers.
3. **Reviewer.** This call fact-checks the script against the sources, polishes the Arabic,
   strips any investment advice and corrects the length. It repeats while the length is outside
   ±10% of `8 min × 130 wpm`.

Two more passes follow. A **listener-side critic** (a "head of news" prompt) scores the script 1–10 on
hook, clarity, pacing, flow, Arabic and value against `config/style_guide.md`; any score under 8 sends
the reviewer back in with the critic's three fixes, up to two rounds (`critique.json`). Then a
**source map** attributes every spoken sentence to the items it draws on and lists unsourced claims
first (`source_map.md`); the review issue shows the scores and the unsourced count.
`config/style_guide.md` (register, numbers, names, pacing, approved terms, tashkeel policy, what is
never said) is injected into the writer, reviewer and critic on every run — edit it there, nowhere else.

All three calls use `claude-opus-5-5` at `effort: xhigh`. They opt into server-side refusal
fallbacks and check `stop_reason`, so a truncated or refused script fails loudly. It is never
rendered. Newsletter and tweet text is fenced as untrusted data in every prompt.

**Phase 3: video.** `[Pause]` markers become `<break time="0.8s"/>`. Set `pause_style: ellipsis`
if your voice doesn't support SSML. All other markers are removed from the speech and written to
`cue_sheet.json`, with estimated timestamps for your editor. The text is split on Arabic sentence
boundaries.
- **HeyGen:** one scene per chunk with the same avatar and voice, stitched into one MP4.
- **ElevenLabs + D-ID:** `eleven_multilingual_v2` with `previous_text`/`next_text` keeps the
  intonation continuous across chunks. The MP3 is uploaded to D-ID and rendered with your
  `presenter_id`. Check the maximum clip length on your D-ID plan. If 8 minutes is over it, render
  one clip per chunk and join them with `ffmpeg -f concat`.

Job submissions are never retried automatically, because a lost response could otherwise bill a
second render. Status polls and downloads are retried.

**Phase 4: post-production (optional, offline).** `faster-whisper` transcribes the rendered
Arabic audio with word timestamps → `subtitles.srt`, compares it with the approved script (a low
similarity score means the provider dropped or garbled a chunk), then ffmpeg burns the captions in
with proper RTL shaping (`final_subtitled.mp4`) and cuts 9:16 Shorts from the ranges you pass.
Needs `ffmpeg` and an Arabic font (`apt install ffmpeg fonts-noto-core`); the Whisper model is
downloaded from huggingface.co on first run (`WHISPER_MODEL=small` for a quick test).

## Brand assets (`assets/`, rendered offline from code)

| File | What |
|---|---|
| `intro_sting.mp4` | 5 s channel opener, 1080p60, synthesized house bed + SFX mastered to -14 LUFS. Navy matches the avatar background so it cuts straight into the presenter. |
| `intro_sting_poster.png` | Frame at 4.35 s (title lockup) for thumbnails/end cards. |
| `lower_third_presenter.webm` / `.mov` | 6 s name + title lower-third with alpha (VP9 / ProRes 4444; the .mov is regenerated, not committed). Overlay bottom-right in any editor. |
| `lower_third_presenter.png` | Static hold frame of the same lower-third. |

Sources: `sting/` (motion-reel film: `film.js`, `docs/shotlist.md`, `docs/critique.md`, fonts) and `lowerthird/`.
Rebuild the lower-third for a guest or topic: `node scripts/render_alpha.mjs --film lowerthird --name "اسم الضيف" --title "المسمّى" --out guest`
(needs `npm i -D playwright@1.56.1` and ffmpeg). Fonts: Noto Kufi Arabic (display) + Noto Naskh Arabic (UI), OFL.

## Things to verify before the first production run

- **Feed URLs:** newsletters move their feeds, and AlphaSignal is email-only. Point it at a
  Kill the Newsletter Atom feed, as described in `settings.yaml`.
- **X API tier:** reading timelines needs a paid tier. A run reads at most
  `accounts × max_posts_per_account` posts.
- **Arabic speaking pace:** time one real render and set `words_per_minute` to match your twin's
  voice. All the length targets come from this number.
- **Provider API shapes:** the HeyGen v2, ElevenLabs and D-ID endpoints match their current docs.
  Run `--dry-run` and then one short test render before scheduling.

## Disclosure

YouTube requires creators to disclose realistic altered or synthetic content. Tick the
"Altered or synthetic content" box on every upload, and consider a brief on-screen note such as
«يقدّم هذه الحلقة نسخة رقمية من المقدّم مولّدة بالذكاء الاصطناعي». Viewers and enterprise
sponsors also tend to trust a channel more when it is open about using a digital twin.

### Critic: rubric-scored, double-sampled

`config/critic_rubric.md` fixes what counts as a defect on each axis (hook, clarity, pacing,
flow, arabic, value) and its severity. The critic lists defects with quotes; the score is
computed from defect density per segment (penalty 2·major + minor; score 10 − 2·penalty/segments), so every number has evidence behind it. Each round samples
the critic `critic.samples` times (default 2); if any axis differs by more than
`critic.max_disagreement`, a third sample breaks the tie and the per-axis median stands.
`critique.json` keeps every sample and a `stable` flag; the review issue shows them.
Edit the rubric to change the standard; do not tune the bar to chase a score.

### YouTube channels as leads

`ingestion.youtube.channels` in `config/settings.yaml` lists AI news channels by handle. Each
channel's Atom feed is read without an API key; handles are resolved to channel ids once and
cached in `data/youtube_channels.json` (committed by the weekly run). Videos enter as
`source_type: youtube` with a weight under 1, so they surface a story but a written source on
the same story outranks them. Add a channel with one line; set `channel_id` directly to skip
the handle lookup.
