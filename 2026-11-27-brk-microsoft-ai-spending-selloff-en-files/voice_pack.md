# Voice-first pack · 2026-11-27-brk-microsoft-ai-spending-selloff-en

1 chunks · about 0.5 min of speech, 0 s of face · ≈ 1 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-27-brk-microsoft-ai-spending-selloff-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 468 chars)

```
Microsoft shares are down about 13% from their all-time highs. Yahoo Finance reports investors worry about AI spending. Microsoft spent $45.2 billion on capex last quarter to add computing capacity. Free cash flow still stayed positive at $18.6 billion. Azure revenue grew 48% from a year earlier. Microsoft holds 21% of the global cloud infrastructure market, behind Amazon. Nearly 4 million companies use Microsoft 365. Is your company already using Copilot at work?
```
