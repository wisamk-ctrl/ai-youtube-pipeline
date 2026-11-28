# Voice-first pack · 2026-11-28-exp-shirudo-runtime-shields-en

1 chunks · about 0.5 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-28-exp-shirudo-runtime-shields-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 480 chars)

```
OpenAI and Cisco want to shield servers before patches arrive. Testing and deploying a patch can take days or weeks, OpenAI says. Cisco's Thomas Graf says some flaws are now exploited before disclosure. Their open-source answer is Shirudo, Japanese for shield. Teams test whether a shield blocks the flaw but lets real requests through. OpenAI says, in a controlled test, a shield stopped Java4Shell without a restart. Would your team let AI agents write shields for your servers?
```
