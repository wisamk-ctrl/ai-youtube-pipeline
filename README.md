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

## Weekly run

```bash
python run_pipeline.py all                         # ingest + script, then stops for review
# read / edit output/<week>/script.md
python run_pipeline.py video --dry-run             # inspect tts_text.txt and cue_sheet.json (free)
python run_pipeline.py video                       # paid render → output/<week>/talking_head.mp4
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

**Phase 2: scripting (Claude).** This phase is a chain of three calls, each doing one job:
1. **Editor.** `messages.parse` returns a validated Pydantic `EditorialPlan`: 5–7 stories,
   their order, the enterprise angle and B-roll ideas. Item IDs that don't exist are removed.
2. **Writer.** A streamed call writes the full MSA script with `[Pause]`, `[Show B-Roll: …]`,
   `[On-Screen Text: …]` and `[Section: …]` markers.
3. **Reviewer.** This call fact-checks the script against the sources, polishes the Arabic,
   strips any investment advice and corrects the length. It repeats while the length is outside
   ±10% of `8 min × 130 wpm`.

All three calls use `claude-opus-5-5` at `effort: high`. They opt into server-side refusal
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
