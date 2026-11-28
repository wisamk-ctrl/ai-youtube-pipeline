# Voice-first pack · 2026-11-23-brk-openai-shared-ai-limits-en

1 chunks · about 0.8 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-23-brk-openai-shared-ai-limits-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 709 chars)

```
OpenAI's chief scientist Jakub Pachocki wants rival AI labs to agree on limits for their most powerful models. In an essay published November 22, he proposes common limits based on perplexity and other measurements. Perplexity scores how well a model guesses the next piece of text. OpenAI published its own scores for the first time, falling from about 0.99 for GPT-3.5 to under 0.8 for its newest models. Labs would stay below the limits until they can understand and monitor model behavior. CEO Sam Altman backed the idea. Reports name no limit value, no start date, and no body to run it. For Gulf governments building AI capacity, watch whether shared limits become a standard they're expected to follow.
```
