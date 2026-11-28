# Voice-first pack · 2026-11-25-brk-openai-openworks-pilot-en

1 chunks · about 0.5 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-25-brk-openai-openworks-pilot-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 453 chars)

```
OpenAI is paying locals to bring AI to small businesses. The pilot, called OpenWorks, runs in 20 U.S. cities, The Rundown reports. Helpers, called partners, can receive stipends of up to $8,000 a month. Owners pick a task, and the help comes at no cost. Businesses also get three free months of ChatGPT Business. OpenAI's rules exclude software companies and firms backed by venture capital. Would local AI helpers speed up small businesses in the Gulf?
```
