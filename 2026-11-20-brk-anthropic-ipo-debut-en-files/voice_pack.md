# Voice-first pack · 2026-11-20-brk-anthropic-ipo-debut-en

1 chunks · about 0.8 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-20-brk-anthropic-ipo-debut-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 674 chars)

```
Anthropic, the company behind the Claude AI models, is now a public company. Yahoo Finance reports it sold 980 million shares at $83 each, above the $70 to $78 range it had marketed. That valued Anthropic at about $1.5 trillion on a fully diluted basis. The BBC says shares closed 17% higher on day one at $97.17, even as the wider tech sector fell 2.4%. Third-quarter revenue hit $16.96 billion, up 47% from the prior quarter. But the company still runs at an operating loss. It has committed to spending about $895 billion, with roughly half promised by 2030. For the Gulf, watch whether this new capital flows into data centers and compute partnerships across the region.
```
