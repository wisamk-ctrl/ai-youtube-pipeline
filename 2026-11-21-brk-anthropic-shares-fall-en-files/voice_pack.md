# Voice-first pack · 2026-11-21-brk-anthropic-shares-fall-en

1 chunks · about 0.7 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-21-brk-anthropic-shares-fall-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 607 chars)

```
Anthropic's shares fell on Friday, a day after its stock market debut, the BBC reports. On Thursday, trading started at $111.50 and the stock closed up 17% at $97.17. On Friday it dropped more than 12% at one point, to about $85, near the $83 IPO price. It closed down 8.5%, reversing half of Thursday's gains. The Nasdaq plunged 5.3%, and the S&P 500 and the Dow entered correction territory. The BBC cites concerns over AI spending, with more than $1 trillion spent in the last year by a few major tech companies. For the Gulf, watch whether investor nerves change the pace of AI and data center projects.
```
