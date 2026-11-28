# Voice-first pack · 2026-11-25-brk-anthropic-below-ipo-price-en

1 chunks · about 0.5 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-25-brk-anthropic-below-ipo-price-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 467 chars)

```
Anthropic shares have fallen below their $83 IPO price. TechCrunch reports the stock traded as low as $76 by midday Tuesday. That's down nearly 12% from Monday's close. Observers see it as a barometer for AI valuations. TechCrunch says a weak run could pressure startup valuations and AI IPOs. Nvidia also fell more than 7% by midday. The Motley Fool says nine-month revenue surged 1,200% to $33.24 billion. Does this change how your company chooses its AI providers?
```
